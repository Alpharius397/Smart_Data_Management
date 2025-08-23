import axios from 'axios';
import { getAccessToken, getRefreshToken, setAccessToken, setRefreshToken } from '../storage'
import { validNumber, validString } from '../zod';
import z from 'zod';

const BASE_URL = 'http://127.0.0.1:8000/api';  
export const URL = {
    AUTH: { // auth/
        USER: `${BASE_URL}/auth/user`,
        LOGIN: `${BASE_URL}/auth/login`,
        REGISTER: `${BASE_URL}/auth/register`,
        UNIVERSITY: `${BASE_URL}/auth/university`,
        INSTITUTE: `${BASE_URL}/auth/institute`,
        BRANCH: `${BASE_URL}/auth/branch`,
    },
    CARD: { // card
        STATUS: `${BASE_URL}/card/status`, // checks whether or not user owns card
        CARDS: `${BASE_URL}/card/`, // returns all cards owned by user
        HEADING: `${BASE_URL}/card/heading`, // returns a heading
    },
    CHANGE: { // change/
        OTP: { // these send otps
            USERNAME: `${BASE_URL}/change/mail/username`,
            EMAIL: `${BASE_URL}/change/mail/email`,
            PASSWORD: `${BASE_URL}/change/mail/password`,
            DELETE: `${BASE_URL}/change/mail/delete`,
            /** remember redirect user to password screen */
            FORGOT: `${BASE_URL}/change/forgot`,
        },
        /** these verify otp and make changes */
        VERIFY: { 
            USERNAME: `${BASE_URL}/change/username`,
            EMAIL: `${BASE_URL}/change/email`,
            PASSWORD: `${BASE_URL}/change/password`,
            DELETE: `${BASE_URL}/change/delete`,
            /** remember redirect user to password screen */
            FORGOT: `${BASE_URL}/change/reset`,
        }

    },
    REPORT: function (cardID: string, sem:string){ // report/ -> these are dynamic, function call this
        const card = validString.parse(`${cardID}`);
        const Sem = z.string().nullable().parse(sem);

        return `${BASE_URL}/report/${card}?sem=${Sem}`
    }
}

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

        try {
            const {access, refresh} = response.data;
    
            if((access !== undefined) && (access !== null)) await setAccessToken(access); 
            if((refresh !== undefined) && (refresh !== null)) await setRefreshToken(refresh); 

        } catch(err){
            console.warn(err);
        }
        
        return response;    
    }
);

export default Axios

