import { getGenericPassword, setGenericPassword, resetGenericPassword, UserCredentials } from 'react-native-keychain';

const ACCESS_TOKEN = 'access';
const REFRESH_TOKEN = 'refresh';

async function getValue(service: string): Promise<UserCredentials | null> {
    try{

        const token =  await getGenericPassword({ service: service }); 
        
        if(token === false) throw new Error("Failed to retrieve token");
        else {
            return token;
        }

    }
    catch(error){
        console.warn("Async Storage Error: ",error);
        return null;
    }
}

async function removeValue(service: string): Promise<boolean> {
    try{
        const token =  await resetGenericPassword({ service: service }); 
        return token 
    }
    catch(error){
        console.warn("Async Storage Error: ",error);
        return false;
    }
}

async function setValue(name: string, value: string, service: string): Promise<boolean> {
    try{
        const token =  await setGenericPassword(name, value, { service: service }); 
        console.log("Saving Value: ",value);

        if(token === false) throw new Error("Failed to save token");
        else {
            return true;
        }
    }
    catch(error){
        console.warn("Async Storage Error: ",error);
        return false;
    }
}

export async function getAccessToken(): Promise<string | null> {
    const cred = await getValue(ACCESS_TOKEN);
    
    if(cred == null) return null;
    else return cred.password;
}

export async function getRefreshToken(): Promise<string | null> {
    const cred = await getValue(ACCESS_TOKEN);
    
    if(cred == null) return null;
    else return cred.password;
}

export async function removeAccessToken(): Promise<boolean> {
    return await removeValue(ACCESS_TOKEN);
}

export async function removeRefreshToken(): Promise<boolean> {
    return await removeValue(REFRESH_TOKEN);
}

export async function setAccessToken(value: string): Promise<boolean> {
    return await setValue(ACCESS_TOKEN, value, ACCESS_TOKEN);
}

export async function setRefreshToken(value: string): Promise<boolean> {
    return await setValue(REFRESH_TOKEN, value, REFRESH_TOKEN);
}