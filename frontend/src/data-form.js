import { useState } from 'react';
import {
    Box,
    TextField,
    Button,
} from '@mui/material';
import axios from 'axios';


const endpointMapping = {
    'Notion': 'notion',
    'Airtable': 'airtable',
    'Hubspot': 'hubspot',
};

export const DataForm = ({ integrationType, credentials }) => {
    const [loadedData, setLoadedData] = useState(null);
    const endpoint = endpointMapping[integrationType];

    const handleLoad = async () => {
        try {
            const formData = new FormData();
            formData.append('credentials', JSON.stringify(credentials));
            const response = await axios.post(`http://localhost:8000/integrations/${endpoint}/load`, formData);
            const data = response.data;
            setLoadedData(data);
        } catch (e) {
            alert(e?.response?.data?.detail);
        }
    }

    return (
        <Box display='flex' justifyContent='center' alignItems='center' flexDirection='column' width='100%'>
            <Box display='flex' flexDirection='column' width='100%'>
                <Button
                    onClick={handleLoad}
                    sx={{mt: 2}}
                    variant='contained'
                >
                    Load Data
                </Button>
                <Button
                    onClick={() => setLoadedData(null)}
                    sx={{mt: 1}}
                    variant='contained'
                >
                    Clear Data
                </Button>
                {Array.isArray(loadedData) && loadedData.length > 0 && (
                    <Box sx={{ mt: 2 }}>
                        {loadedData.map((item, idx) => (
                            <pre key={item.id || idx} style={{ margin: 0 }}>
                {`${item.name}:
                    Type: ${item.type}
                    ID: ${item.id}
                    Parent ID: ${item.parent_id || 'N/A'}
                    Parent path/name: ${item.parent_name || 'N/A'}`}
                            </pre>
                        ))}
                    </Box>
                )}
                {loadedData && Array.isArray(loadedData) && loadedData.length === 0 && (
                    <div>No data found</div>
                )}
            </Box>
        </Box>
    );
}