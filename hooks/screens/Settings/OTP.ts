import { useEffect, useState } from 'react';
import {onErrorType, onFailureType, onSuccessType, useAuthHook} from '../..';
import { URL } from '../../../axios';
import { DEFAULT_ERROR, OTP_RETRY_TIMEOUT } from '../../../constants';
import { showAlert } from '../../../utils/alert';
import z from 'zod';

type ChangeType = 'username' | 'password' | 'email' | 'delete' | 'forgot'

function getMailUrl(type: ChangeType){
    switch(type){
        case 'username': return URL.CHANGE.OTP.USERNAME;
        case 'password': return URL.CHANGE.OTP.PASSWORD;
        case 'email': return URL.CHANGE.OTP.EMAIL;
        case 'delete': return URL.CHANGE.OTP.DELETE;
        case 'forgot': return URL.CHANGE.OTP.FORGOT;
        default: throw new Error("Invalid OTP type")
    }
}

function getChangeUrl(type: ChangeType){
    switch(type){
        case 'username': return URL.CHANGE.VERIFY.USERNAME;
        case 'password': return URL.CHANGE.VERIFY.PASSWORD;
        case 'email': return URL.CHANGE.VERIFY.EMAIL;
        case 'delete': return URL.CHANGE.VERIFY.DELETE;
        case 'forgot': return URL.CHANGE.VERIFY.FORGOT;
        default: throw new Error("Invalid OTP type")
    }
}

export function useOTP(type: ChangeType, onSuccess: onSuccessType, onFailure: onFailureType, onError: onErrorType) {
    return useAuthHook(getMailUrl(type), 'POST', onSuccess, onFailure, onError)
}

export function useChangeHook(type: ChangeType, onSuccess: onSuccessType, onFailure: onFailureType, onError: onErrorType) {
    return useAuthHook(getChangeUrl(type), 'POST', onSuccess, onFailure, onError);
}

export function useOtpHook(type: ChangeType): [number, () => void] {

    const otpSuccess = () => {
        showAlert("OTP Alert", "OTP has been sent to your registered email!");
    };
    
    const otpFailure = (error: string[]) => {
        showAlert("OTP Alert", "Failed to send OTP due to: " + error.join('\n'));
    };
    
    const otpError = () => {
        showAlert("OTP Alert", DEFAULT_ERROR);
    };
    
    const [sendOTP, isPending] = useOTP(type, otpSuccess, otpFailure, otpError);
    const [timer, setTimer] = useState<number>(OTP_RETRY_TIMEOUT);

    const handleSendOTP = () => {
        sendOTP({data: {}, validator: z.object({}) });
        setTimer(30);
    };

    useEffect(() => {

        if(isPending) return;

        let interval: NodeJS.Timeout;
        if (timer > 0) {
            interval = setInterval(() => setTimer(prev => prev - 1), 1000);
        }
        return () => clearInterval(interval);
    }, [timer]);
    
    useEffect(() => {
        sendOTP({data: {}, validator: z.object()});
    }, []);

    return [timer, handleSendOTP]
}

export function useForgotOtpHook(email: string): [number, () => void] {

    const otpSuccess = () => {
        showAlert("OTP Alert", "OTP has been sent to the given email!");
    };
    
    const otpFailure = (error: string[]) => {
        showAlert("OTP Alert", "Failed to send OTP due to: " + error.join('\n'));
    };
    
    const otpError = () => {
        showAlert("OTP Alert", DEFAULT_ERROR);
    };
    
    const [sendOTP] = useOTP('forgot', otpSuccess, otpFailure, otpError);
    const [timer, setTimer] = useState<number>(10);

    const handleSendOTP = () => {
        sendOTP({data: {email}, validator: z.object({email: z.email()})});
        setTimer(10);
    };

    useEffect(() => {

        let interval: NodeJS.Timeout;
        if (timer > 0) {
            interval = setInterval(() => setTimer(prev => prev - 1), 1000);
        }
        return () => clearInterval(interval);
    }, [timer]);
    
    return [timer, handleSendOTP]
}

