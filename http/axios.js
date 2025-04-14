import axios, { AxiosError, AxiosResponse, InternalAxiosRequestConfig } from 'axios';
import { getAccessToken } from '../storage/storage'


const BASE_URL = 'http://127.0.0.1:8000/';

export const LOGIN = 'mobile/auth/login/';
export const REGISTER = 'mobile/auth/register/';
export const REFRESH = 'mobile/auth/refresh/';
export const SUBSCRIBER = 'mobile/subscriber/'

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
            if (token!==null && config.headers) {
                config.headers.Authorization = `Bearer ${token}`;
            }
        } catch (error) {
            console.error('Error fetching token:', error);
        }
        return config;
    },

    (error) => {
        console.error('Request interceptor error:', error);
        return Promise.reject(error);
    }
);

Axios.interceptors.response.use(
    (response) => {
        return response;    
    }
);

export default Axios

