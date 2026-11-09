// frontend/src/api.js

import toast from 'react-hot-toast';

const API_URL = 'http://127.0.0.1:8000';


// ============================================================
// Generic authenticated fetch helper
// ============================================================

const fetchWithAuth = async (url, options = {}) => {
    const token = localStorage.getItem('accessToken');

    const isFormData = options.body instanceof FormData;

    const headers = {
        ...options.headers,
    };

    // Do NOT manually set Content-Type for FormData.
    // The browser automatically adds the multipart boundary.
    if (!isFormData) {
        headers['Content-Type'] = 'application/json';
    }

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    try {
        const response = await fetch(url, {
            ...options,
            headers,
        });

        if (!response.ok) {
            const errorData = await response
                .json()
                .catch(() => ({
                    detail: response.statusText,
                }));

            console.error(
                `API Error: ${response.status}`,
                errorData
            );

            // Token expired / invalid
            if (response.status === 401) {
                localStorage.removeItem('accessToken');
                window.location.reload();
                return null;
            }

            // Show validation details properly
            if (response.status === 422) {
                console.error(
                    'FastAPI validation error:',
                    errorData.detail
                );
            }

            const detail = Array.isArray(errorData.detail)
                ? errorData.detail
                    .map((item) => {
                        if (typeof item === 'string') {
                            return item;
                        }

                        return item.msg || 'Validation error';
                    })
                    .join(', ')
                : errorData.detail ||
                  'An unknown error occurred.';

            // ✅ Use toast instead of alert
            toast.error(detail, { duration: 5000 });

            return null;
        }

        // No content
        if (
            response.status === 204 ||
            response.headers.get('content-length') === '0'
        ) {
            return {
                success: true,
            };
        }

        return await response.json();

    } catch (error) {
        console.error(
            'Network or fetch error:',
            error
        );

        // ✅ Use toast instead of alert
        toast.error('Network error. Could not connect to the server.', {
            duration: 5000,
        });

        return null;
    }
};


// ============================================================
// Register
// ============================================================

export async function handleRegister(userData) {
    return await fetchWithAuth(
        `${API_URL}/register`,
        {
            method: 'POST',
            body: JSON.stringify(userData),
        }
    );
}


// ============================================================
// Login
// ============================================================

export async function handleLogin(
    identifier,
    password
) {
    return await fetchWithAuth(
        `${API_URL}/token`,
        {
            method: 'POST',
            body: JSON.stringify({
                identifier,
                password,
            }),
        }
    );
}


// ============================================================
// Profile
// ============================================================

export async function getProfile() {
    return await fetchWithAuth(
        `${API_URL}/me`
    );
}


// ============================================================
// Custom instruction
// ============================================================

export async function updateCustomInstruction(
    instruction
) {
    return await fetchWithAuth(
        `${API_URL}/me/instruction`,
        {
            method: 'PUT',
            body: JSON.stringify({
                instruction,
            }),
        }
    );
}


// ============================================================
// Chat history
// ============================================================

export async function getAllSessions() {
    return await fetchWithAuth(
        `${API_URL}/history`
    );
}


export async function getChatMessages(
    sessionId
) {
    return await fetchWithAuth(
        `${API_URL}/history/${sessionId}`
    );
}


export async function deleteSession(
    sessionId
) {
    return await fetchWithAuth(
        `${API_URL}/history/${sessionId}`,
        {
            method: 'DELETE',
        }
    );
}


// ============================================================
// Rename Session
// ============================================================

export async function renameSession(sessionId, title) {
    return await fetchWithAuth(
        `${API_URL}/history/${sessionId}/rename`,
        {
            method: 'PATCH',
            body: JSON.stringify({ title }),
        }
    );
}


// ============================================================
// Send Chat Message
// ============================================================

export async function sendMessage(payload) {

    const formData = new FormData();


    // --------------------------------------------------------
    // Prompt
    // --------------------------------------------------------

    formData.append(
        'prompt',
        payload.prompt || ''
    );


    // --------------------------------------------------------
    // Image
    // --------------------------------------------------------

    if (payload.imageFile) {
        formData.append(
            'image',
            payload.imageFile
        );
    }


    // --------------------------------------------------------
    // Existing session
    // --------------------------------------------------------

    if (
        payload.sessionId !== null &&
        payload.sessionId !== undefined &&
        payload.sessionId !== ''
    ) {
        formData.append(
            'session_id',
            String(payload.sessionId)
        );
    }


    // --------------------------------------------------------
    // Personality
    // --------------------------------------------------------

    if (
        payload.personality !== null &&
        payload.personality !== undefined &&
        payload.personality !== ''
    ) {
        formData.append(
            'personality',
            payload.personality
        );
    }


    // --------------------------------------------------------
    // Deep Research
    //
    // IMPORTANT:
    // Always send a valid boolean string.
    // Never send undefined.
    // --------------------------------------------------------

    const isDeepResearch =
        payload.isDeepResearch === true;

    formData.append(
        'is_deep_research',
        isDeepResearch ? 'true' : 'false'
    );


    // --------------------------------------------------------
    // Debug information
    // --------------------------------------------------------

    console.log(
        '[API] Sending chat request:',
        {
            prompt: payload.prompt,
            sessionId: payload.sessionId,
            personality: payload.personality,
            isDeepResearch,
            hasImage: !!payload.imageFile,
        }
    );


    // --------------------------------------------------------
    // Send request
    // --------------------------------------------------------

    return await fetchWithAuth(
        `${API_URL}/chat/`,
        {
            method: 'POST',
            body: formData,
        }
    );
}