import Axios, { URL } from '../axios';
import { isAxiosError } from 'axios';
import { AuthResponse, QueryAuthType, zodError } from '../zod';
import { UseMutateFunction, useMutation } from '@tanstack/react-query';
import * as z from "zod";

type Data = {
    [key: string]: any
}
/** Data and it's validator */
type Config = {data: Data, validator: z.ZodObject };
type RequestMethod = 'GET' | 'POST' | 'PUT' | 'DELETE';
export type onSuccessType = () => void;
export type onFailureType = (warning: string[]) => void;
export type onErrorType = () => void;

function getAxiosMethod(method: RequestMethod){
    switch(method){
        case 'GET': return Axios.get;
        case 'PUT': return Axios.put;
        case 'POST': return Axios.post;
        case 'DELETE': return Axios.delete;
        default: throw new Error("Invalid Request Method");
    }
}

async function process(config: Config, url: string, method: RequestMethod): Promise<QueryAuthType> {

    try {   
        let data = await config.validator.parseAsync(config.data);
        const response = await getAxiosMethod(method)(url, data);
        await AuthResponse.parseAsync(response.data);
        return {type: "success", "status": true, "error": []};

    } catch(Error){

        if(Error instanceof zodError){
            return {type: "validation-error", error: (Error.issues).map((value) => value.message)};
        }

        if(isAxiosError(Error)){
            try {
                let { error } = await AuthResponse.parseAsync(Error.response.data)

                if(Error.response?.status !== 500){
                    return { type: "failure", status: false, error };
                }
                else{
                    return {type: "server-error"};
                }
            } catch(err) {
                console.warn(err);
                return {type: "server-error"};
            }
        } else {
            return { type: "server-error" };
        }
    }
}

/** Our **_does everything_** function factory */
export function useAuthHook(
        url: string,
        method: RequestMethod, 
        onSuccess: onSuccessType, 
        onFailure: onFailureType, 
        onError: onErrorType
    ): [UseMutateFunction<QueryAuthType, Error, Config, unknown>, boolean ] {

    const {mutate, isPending} = useMutation({
        mutationFn: (config: Config) => process(config, url, method),
        onSuccess: (result) => {
            switch (result.type) {
            case 'failure':
                onFailure(result.error);
                break;
            case 'success':
                onSuccess();
                break;
            case 'validation-error':
                onFailure(result.error);
                break;
            case 'server-error':
                onError();
                break;
            }
        },
    });

    return [mutate, isPending];
}