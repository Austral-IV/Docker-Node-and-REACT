# Simple full stack app making use of Docker, Node.js, React and Redis

The GUI is attrocious. I have yet to explore React in that facility. However, it's still a functional (simple) applicatoin where you can connect through OAuth2 to your airtable, hubspot or notion account and display some information.

## How to build

### With Docker:

The Dockerfiles on `frontend` and `backend` contain all the instructions necesary for docker to launch the app. Critically, the correct ports have to be exposed.

Just run 

    docker compose up

Although I reccomend

    docker compose up --build

which rebuilds the layers if there are any changes in the code, otherwise uses the cache and behaves like the first command.

### Before Docker:

#### hubspot.py:

All integrations work mostly in the same way, for example, hubspot.py:

- authorize_hubspot: creates authentication URL in accordance with the [guide in docs](https://developers.hubspot.com/docs/guides/apps/authentication/oauth-quickstart-guide)

- oauth2callback_hubspot: handles the OAuth2 callback after the user authorizes the app.

- get_hubspot_credentials: Fetches credentials from redis (or memurai, so long as it's in the default port)

- create_integration_item_metadata_object: Creates an InteractionItem object, universal format accross integrations. 

- get_items_hubspot: set to fetch contacts and companies. Items are displayed on the web app as well as the console (weherever `uvicorn main:app --reload` was run)

#### Other steps

These are non-code things I had to do to get this to run on my machine. If you've already used `npm` and `uvicorn` before, as well as the working `venv` and `redis`, you should be clear.

**Frontend:**

with an nvm version managers

    nvm use [version]
    npm i
    npm run start

**Backend:**

    python -m venv .venv
    .venv\Scripts\activate
    pip install -r requirements.txt
    pip install setuptools requests redis fastapi uvicorn kombu httpx python-multipart

now you can run 

    uvicorn main:app --reload

**Other Tools**
- nvm version manager: [nvm-windows](https://github.com/coreybutler/nvm-windows).
- Created a developer account on [Hubspot](https://developers.hubspot.com) and an App in the same, obtaining client ID and client secret.
- Used [Memurai](https://www.memurai.com/get-memurai) as a stand-in for Redis. Should be functionally the same. Note: with docker, I just used the redis image available