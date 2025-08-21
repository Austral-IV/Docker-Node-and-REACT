import datetime
import json
import secrets
from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse
import httpx
import asyncio
import base64
import hashlib

import requests
from integrations.integration_item import IntegrationItem

from redis_client import add_key_value_redis, get_value_redis, delete_key_redis

# hubspot.py
CLIENT_ID =  '2f168657-3e97-4161-84f4-ed8c7cbfc520'
CLIENT_SECRET = '69e43ae9-c99f-48d7-8515-ec8453ed2824'
encoded_client_id_secret = base64.b64encode(f'{CLIENT_ID}:{CLIENT_SECRET}'.encode()).decode()

REDIRECT_URI = 'http://localhost:8000/integrations/hubspot/oauth2callback'
SCOPE = 'oauth%20crm.objects.contacts.read%20crm.objects.contacts.write%20crm.objects.companies.read%20crm.objects.companies.write'

async def authorize_hubspot(user_id, org_id):
    state_data = {
        'state': secrets.token_urlsafe(32),
        'user_id': user_id,
        'org_id': org_id
    }
    encoded_state = json.dumps(state_data)
    await add_key_value_redis(f'hubspot_state:{org_id}:{user_id}', encoded_state, expire=600)
    authorization_url = f"https://app.hubspot.com/oauth/authorize?client_id={CLIENT_ID}&scope={SCOPE}&redirect_uri={REDIRECT_URI}&state={encoded_state}"
    return authorization_url

async def oauth2callback_hubspot(request: Request):
    # Check for error in the request
    if request.query_params.get('error'):
        raise HTTPException(status_code=400, detail=request.query_params.get('error_description'))
    code = request.query_params.get('code')
    encoded_state = request.query_params.get('state')
    state_data = json.loads(encoded_state)
    
    # Decode redis state data
    original_state = state_data.get('state')
    user_id = state_data.get('user_id')
    org_id = state_data.get('org_id')

    saved_state = await get_value_redis(f'hubspot_state:{org_id}:{user_id}')

    if not saved_state or original_state != json.loads(saved_state).get('state'):
        raise HTTPException(status_code=400, detail='State does not match.')
    
    async with httpx.AsyncClient() as client:
        response, _ = await asyncio.gather(
            client.post(
            'https://api.hubapi.com/oauth/v1/token',
            data={
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': REDIRECT_URI,
                'client_id': CLIENT_ID,
                'client_secret': CLIENT_SECRET,
            },
            headers={
                'Authorization': f'Basic {encoded_client_id_secret}',
                'Content-Type': 'application/x-www-form-urlencoded'
                },
            ),
            delete_key_redis(f'hubspot_state:{org_id}:{user_id}'),
        )
        await add_key_value_redis(f'hubspot_credentials:{org_id}:{user_id}', json.dumps(response.json()), expire=600)
    close_window_script = """
    <html>
        <script>
            window.close();
        </script>
    </html>
    """
    return HTMLResponse(content=close_window_script)

async def get_hubspot_credentials(user_id, org_id): # memurai 
    credentials = await get_value_redis(f'hubspot_credentials:{org_id}:{user_id}')
    if not credentials:
        raise HTTPException(status_code=400, detail='No credentials found.')
    credentials = json.loads(credentials)
    if not credentials:
        raise HTTPException(status_code=400, detail='No credentials found in json either.')
    await delete_key_redis(f'hubspot_credentials:{org_id}:{user_id}')

    return credentials

def create_integration_item_metadata_object(
    response_json: dict, item_type: str, parent_id=None, parent_name=None
) -> IntegrationItem:
    """ Creates an InteractionItem object, universal format accross integrations. """
    parent_id = None if parent_id is None else parent_id + '_Base'
    integration_item_metadata = IntegrationItem(
        id=response_json.get('id', None) + '_' + item_type,
        name=response_json.get('name', None),
        type=item_type,
        parent_id=parent_id,
        parent_path_or_name=parent_name,
    )
    return integration_item_metadata

async def get_items_hubspot(credentials):
    credentials = json.loads(credentials)
    access_token = credentials.get("access_token")

    if not access_token:
        raise HTTPException(status_code=401, detail="Missing access token")

    print("[HubSpot] Fetching ...")
    print(list)
    headers = {"Authorization": f"Bearer {access_token}"}
    list_of_items = []

    async with httpx.AsyncClient() as client:
        # fetch contacts:
        contacts_resp = await client.get("https://api.hubapi.com/crm/v3/objects/contacts", headers=headers)
        if contacts_resp.status_code == 200:
            contacts = contacts_resp.json().get("results", [])
            for contact in contacts:
                props = contact.get("properties", {})
                full_name = f"{props.get('firstname', '')} {props.get('lastname', '')}".strip()
                item = create_integration_item_metadata_object(
                    response_json={
                        "id": contact.get("id"),
                        "name": full_name or "Unnamed Contact"
                    },
                    item_type="Contact"
                )
                list_of_items.append(item)

        # --- Fetch companies ---
        companies_resp = await client.get("https://api.hubapi.com/crm/v3/objects/companies", headers=headers)
        if companies_resp.status_code == 200:
            companies = companies_resp.json().get("results", [])
            for company in companies:
                props = company.get("properties", {})
                name = props.get("name", "Unnamed Company")
                item = create_integration_item_metadata_object(
                    response_json={
                        "id": company.get("id"),
                        "name": name
                    },
                    item_type="Company"
                )
                list_of_items.append(item)

    print(f"[HubSpot] Fetched {len(list_of_items)} items (contacts + companies)")
    for item in list_of_items:
        print(f"[HubSpot] Item: {item.id}, Name: {item.name}, Type: {item.type}")
    return list_of_items
