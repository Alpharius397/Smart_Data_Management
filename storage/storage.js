import AsyncStorage from '@react-native-async-storage/async-storage';

const ACCESS_TOKEN = 'access';
const REFRESH_TOKEN = 'refresh';

export async function getAccessToken() {
    try{
        const token =  await AsyncStorage.getItem(ACCESS_TOKEN); 
        return token;
    }
    catch(error){
        console.warn("Async Storage Error: ",error);
        return null;
    }
}

export async function getRefreshToken() {
    try{
        const token =  await AsyncStorage.getItem(REFRESH_TOKEN); 
        return token;
    }
    catch(error){
        console.warn("Async Storage Error: ",error);
        return error;
    }
}

export async function removeRefreshToken() {
    try{
        const token =  await AsyncStorage.removeItem(REFRESH_TOKEN); 
        return true;
    }
    catch(error){
        console.warn("Async Storage Error: ",error);
        return false;
    }
}

export async function removeAccessToken() {
    try{
        const token =  await AsyncStorage.removeItem(ACCESS_TOKEN); 
        return true;
    }
    catch(error){
        console.warn("Async Storage Error: ",error);
        return false;
    }
}

export async function setAccessToken(value) {
    try{
        await AsyncStorage.setItem(ACCESS_TOKEN, value); 
        console.log("Saving Value: ",value);
        Promise.resolve(true);
    }
    catch(error){
        console.warn("Async Storage Error: ",error);
        Promise.reject(error);
    }
}

export async function setRefreshToken(value) {
    try{
        await AsyncStorage.setItem(REFRESH_TOKEN, value); 
        console.log("Saving Value: ",value);
        Promise.resolve(true);
    }
    catch(error){
        console.warn("Async Storage Error: ",error);
        Promise.reject(error);
    }
}
