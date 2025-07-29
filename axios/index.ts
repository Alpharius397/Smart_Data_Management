import axios, { AxiosError, AxiosResponse, InternalAxiosRequestConfig } from 'axios';
import { getAccessToken, getRefreshToken, setAccessToken, setRefreshToken } from '../storage'


const BASE_URL = 'http://127.0.0.1:8000/';

export const LOGIN = 'mobile/auth/login/';
export const REGISTER = 'mobile/auth/register/';
export const SUBSCRIBER = 'mobile/subscriber/';
export const CARDS = 'mobile/cards/';

const Axios = axios.create({
    baseURL: BASE_URL,
    headers: {
        'Request-Origin': BASE_URL,
        'Content-Type': 'application/json',
    },
});

Axios.interceptors.request.use(
    async (config) => {
        try {
            const token = await getAccessToken(); 
            const refresh = await getRefreshToken(); 

            if ((token !== null) && (refresh !== null) && (config.headers)) {
                config.headers.Authorization = `Bearer ${token}`;
                config.headers.Refresh = `Bearer ${refresh}`;
            }

        } catch (error) {
            console.error('Error fetching token:', error);
        }
        return config;
    },

    async (error) => {
        console.error('Request interceptor error:', error);
        return Promise.reject(error);
    }
);

Axios.interceptors.response.use(
    async (response) => {
        const {access, refresh} = response.data;
        await setAccessToken(access); 
        await setRefreshToken(refresh); 
        return response;    
    }
);

export default Axios

