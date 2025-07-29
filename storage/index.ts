import { getGenericPassword, setGenericPassword, resetGenericPassword } from 'react-native-keychain';

const ACCESS_TOKEN = 'access';
const REFRESH_TOKEN = 'refresh';

export async function getAccessToken(): Promise<string | null> {
    try{

        const token =  await getGenericPassword({ service: ACCESS_TOKEN}); 
        
        if(token === false) throw new Error("Failed to retrieve token");
        else {
            return token.password;
        }

    }
    catch(error){
        console.warn("Async Storage Error: ",error);
        return null;
    }
}

export async function getRefreshToken(): Promise<string | null> {
    try{
        const token =  await getGenericPassword({ service: REFRESH_TOKEN }); 
        
        if(token === false) throw new Error("Failed to retrieve token");
        else {
            return token.password;
        }
    }
    catch(error){
        console.warn("Async Storage Error: ",error);
        return error;
    }
}

export async function removeAccessToken(): Promise<boolean> {
    try{
        const token =  await resetGenericPassword({ service: ACCESS_TOKEN }); 
        return token 
    }
    catch(error){
        console.warn("Async Storage Error: ",error);
        return false;
    }
}

export async function removeRefreshToken(): Promise<boolean> {
    try{
        const token =  await resetGenericPassword({ service: REFRESH_TOKEN }); 
        return token        
    }
    catch(error){
        console.warn("Async Storage Error: ",error);
        return false;
    }
}


export async function setAccessToken(value: string): Promise<boolean> {
    try{
        const token =  await setGenericPassword(ACCESS_TOKEN, value, { service: ACCESS_TOKEN }); 
        console.log("Saving Value: ",value);

        if(token === false) throw new Error("Failed to retrieve token");
        else {
            return true;
        }
    }
    catch(error){
        console.warn("Async Storage Error: ",error);
        return false;
    }
}

export async function setRefreshToken(value: string): Promise<boolean> {
    try{
        const token =  await setGenericPassword(REFRESH_TOKEN, value, { service: REFRESH_TOKEN }); 
        console.log("Saving Value: ",value);
        
        if(token === false) throw new Error("Failed to retrieve token");
        else {
            return true;
        }
    }
    catch(error){
        console.warn("Async Storage Error: ",error);
        return false;
    }
}
