

import { UserInfoSchema, UserInfo } from '../../../zod/screens/Settings/Profile';
import { useQuery } from '@tanstack/react-query'
import Axios, { URL } from '../../../axios';
import { zodError } from '../../../zod';
import { isAxiosError } from 'axios';
import { DEFAULT_ERROR } from '../../../constants';
import { useMemo } from 'react';


async function fetchInfo(): Promise<UserInfo> {
    try {
        await new Promise((res) => {
            setTimeout(res, 1000);
        })
        const response = await Axios.get(URL.AUTH.USER);

        let a = await UserInfoSchema.parseAsync(response.data);

        return a;

    } catch(err){

        if(err instanceof zodError){
            console.warn(err)
            throw new Error("Received Invalid Data");
        }

        if(isAxiosError(err)){
            try {
                if(err.response?.status !== 500){
                    throw new Error("Unauthorized Fetch detected! Please logout and login")
                }
                else{
                    throw new Error(DEFAULT_ERROR);
                }
            } catch(eRR) {
                console.warn(eRR);
                throw new Error(DEFAULT_ERROR);
                
            }
        } else {
            throw new Error(DEFAULT_ERROR);
        }
    }

}

export function useProfile(){

    const {data, isError, isLoading, refetch} = useQuery({
        queryKey: ['user-info'],
        queryFn: fetchInfo,
    });

    const profileData = useMemo((): UserInfo => {
        let a = data;

        if(a === undefined){
            return {
                username: 'Failed to Fetch',
                email: 'Failed to Fetch',
                university: 'Failed to Fetch',
                institute: 'Failed to Fetch',
                branch: 'Failed to Fetch',
            }
        } else {
            return data;
        }

    }, [data])

    return {profileData, refetch, isLoading, isError};
}