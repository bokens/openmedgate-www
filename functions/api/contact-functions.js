// functions/api/contact.js
// CloudFlare Pages Function - stores at: /functions/api/contact.js

const HUBSPOT_API_KEY = 'aeadca76-4128-4c72-a7c6-260b461c8a75; // Store as env var
const HUBSPOT_PORTAL_ID = '146629432';

export const onRequest = async (context) => {
  const { request } = context;

  // Only allow POST
  if (request.method !== 'POST') {
    return new Response('Method not allowed', { status: 405 });
  }

  // CORS headers
  const headers = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': 'https://openmedgate.com',
    'Access-Control-Allow-Methods': 'POST',
  };

  // Handle preflight
  if (request.method === 'OPTIONS') {
    return new Response(null, {
      headers,
      status: 204,
    });
  }

  try {
    const body = await request.json();

    // Extract fields from payload
    const { fields, context: formContext } = body;

    // Transform to HubSpot contact format
    const hubspotPayload = {
      properties: fields.reduce((acc, field) => {
        acc[field.name] = field.value;
        return acc;
      }, {}),
    };

    // Submit to HubSpot API
    const hubspotResponse = await fetch(
      `https://api.hubapi.com/crm/v3/objects/contacts`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${HUBSPOT_API_KEY}`,
        },
        body: JSON.stringify(hubspotPayload),
      }
    );

    if (!hubspotResponse.ok) {
      const error = await hubspotResponse.text();
      console.error('HubSpot API error:', error);
      throw new Error('HubSpot submission failed');
    }

    const result = await hubspotResponse.json();

    return new Response(
      JSON.stringify({
        success: true,
        contactId: result.id,
      }),
      {
        headers,
        status: 201,
      }
    );
  } catch (error) {
    console.error('Contact form error:', error);

    return new Response(
      JSON.stringify({
        success: false,
        error: error.message,
      }),
      {
        headers,
        status: 500,
      }
    );
  }
};