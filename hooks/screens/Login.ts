import {onErrorType, onFailureType, onSuccessType, useAuthHook} from '..';
import { URL } from '../../axios';

export function useLogin(onSuccess: onSuccessType, onFailure: onFailureType, onError: onErrorType) {
    return useAuthHook(URL.AUTH.LOGIN, 'POST', onSuccess, onFailure, onError)
}