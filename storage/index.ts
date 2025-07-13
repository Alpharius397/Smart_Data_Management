import AsyncStorage from '@react-native-async-storage/async-storage';

const ACCESS_TOKEN = 'access';
const REFRESH_TOKEN = 'refresh';

export async function getAccessToken(): Promise<string | null> {
    try{
        const token =  await AsyncStorage.getItem(ACCESS_TOKEN); 
        return token;
    }
    catch(error){
        console.warn("Async Storage Error: ",error);
        return null;
    }
}

export async function getRefreshToken(): Promise<string | null> {
    try{
        const token =  await AsyncStorage.getItem(REFRESH_TOKEN); 
        return token;
    }
    catch(error){
        console.warn("Async Storage Error: ",error);
        return error;
    }
}

export async function removeRefreshToken(): Promise<boolean> {
    try{
        const token =  await AsyncStorage.removeItem(REFRESH_TOKEN); 
        return true;
    }
    catch(error){
        console.warn("Async Storage Error: ",error);
        return false;
    }
}

export async function removeAccessToken(): Promise<boolean> {
    try{
        const token =  await AsyncStorage.removeItem(ACCESS_TOKEN); 
        return true;
    }
    catch(error){
        console.warn("Async Storage Error: ",error);
        return false;
    }
}

export async function setAccessToken(value: string): Promise<boolean> {
    try{
        await AsyncStorage.setItem(ACCESS_TOKEN, value); 
        console.log("Saving Value: ",value);
        return true;
    }
    catch(error){
        console.warn("Async Storage Error: ",error);
        return false;
    }
}

export async function setRefreshToken(value: string): Promise<boolean> {
    try{
        await AsyncStorage.setItem(REFRESH_TOKEN, value); 
        console.log("Saving Value: ",value);
        return true;
    }
    catch(error){
        console.warn("Async Storage Error: ",error);
        return false;
    }
}
