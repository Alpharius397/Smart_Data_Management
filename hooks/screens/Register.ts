import Axios, { URL } from '../../axios';
import { Item, ItemResponse, validItem } from '../../zod/screens/Register';
import { validNumber } from '../../zod';
import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { onErrorType, onFailureType, onSuccessType, useAuthHook } from '..';


export function useRegister(onSuccess: onSuccessType, onFailure: onFailureType, onError: onErrorType) {
    return useAuthHook(URL.AUTH.REGISTER, 'POST', onSuccess, onFailure, onError);
}

/** Really creative ik */
type Type = 'university' | 'institute' | 'branch'

function AxiosRegisterFactory(type: Type, dependencies: number | null = null){
    const getURL = () => {
        switch(type){
            case 'university': return URL.AUTH.UNIVERSITY;
            case 'institute': return URL.AUTH.INSTITUTE;
            case 'branch': return URL.AUTH.BRANCH;
        }
    };

    const getSubType = () => {
        switch(type){
            case 'university': return {};
            case 'institute': return { 'university': validNumber.parse(dependencies) };
            case 'branch': return { 'institute': validNumber.parse(dependencies) };
        }
    };

    async function requestFunc():Promise<Item> {

        try {
    
            const response = await Axios.get(getURL(), {params: getSubType()});
            const { options }: ItemResponse = response.data;
    
            let a = await validItem.parseAsync(options);
            return a;

        }
        catch(err){
            console.warn(err)
            return [];
        }
    }

    return requestFunc;

}

export function useItems(type: Type, dependencies: number | null = null): Item {

    const { data } = useQuery({
        queryFn: AxiosRegisterFactory(type, dependencies),
        queryKey: [type, dependencies],
    });

    const transform = useMemo(() => {
        let a = validItem.safeParse(data);

        if(a.success === false) return [];

        return a.data;

    }, [data])

    return transform;
}