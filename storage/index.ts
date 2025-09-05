import { getGenericPassword, setGenericPassword, resetGenericPassword, UserCredentials } from 'react-native-keychain';

const ACCESS_TOKEN = 'access';
const REFRESH_TOKEN = 'refresh';
const PRIVATE_KEY = 'private';
const PUBLIC_KEY = 'public';

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
    const cred = await getValue(REFRESH_TOKEN);
    
    if(cred == null) return null;
    else return cred.password;
}

export async function getPrivateKey(): Promise<string | null> {
    const cred = await getValue(PRIVATE_KEY);
    
    if(cred == null) return null;
    else return cred.password;
}

export async function getPublicKey(): Promise<string | null> {
    const cred = await getValue(PUBLIC_KEY);
    
    if(cred == null) return null;
    else return cred.password;
}

export async function removeAccessToken(): Promise<boolean> {
    return await removeValue(ACCESS_TOKEN);
}

export async function removeRefreshToken(): Promise<boolean> {
    return await removeValue(REFRESH_TOKEN);
}

export async function removePrivateKey(): Promise<boolean> {
    return await removeValue(PRIVATE_KEY);
}

export async function removePublicKey(): Promise<boolean> {
    return await removeValue(PUBLIC_KEY);
}

export async function setAccessToken(value: string): Promise<boolean> {
    return await setValue(ACCESS_TOKEN, value, ACCESS_TOKEN);
}

export async function setRefreshToken(value: string): Promise<boolean> {
    return await setValue(REFRESH_TOKEN, value, REFRESH_TOKEN);
}

export async function setPrivateKey(value: string): Promise<boolean> {
    return await setValue(PRIVATE_KEY, value, PRIVATE_KEY);
}

export async function setPublicKey(value: string): Promise<boolean> {
    return await setValue(PUBLIC_KEY, value, PUBLIC_KEY);
}
