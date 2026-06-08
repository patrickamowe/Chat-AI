const API_BASE_URL = 'http://127.0.0.1:8000';
const SIGNIN_URL = `${API_BASE_URL}/auth/signin`;
const SIGNOUT_URL = `${API_BASE_URL}/auth/logout`;
const REFRESH_TOKEN_URL = `${API_BASE_URL}/auth/refresh`;
const SIGNUP_URL = `${API_BASE_URL}/users/signup`;
const USER_INFO_URL = `${API_BASE_URL}/users/profile`;
const VALIDATE_TOKEN_URL = `${API_BASE_URL}/auth/validate`;

export {
    API_BASE_URL,
    SIGNIN_URL,
    SIGNOUT_URL,
    REFRESH_TOKEN_URL,
    SIGNUP_URL,
    USER_INFO_URL,
    VALIDATE_TOKEN_URL

};