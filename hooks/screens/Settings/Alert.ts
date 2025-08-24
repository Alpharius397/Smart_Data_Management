import { useFocusEffect } from "@react-navigation/native";
import React from "react";
import { BackHandler } from "react-native";
import { StackNavigationParam } from "../../../zod/screens";
import { StackNavigationProp } from "@react-navigation/stack";
import { ALERT_TYPE, Dialog } from "react-native-alert-notification";
import { DEFAULT_ERROR } from "../../../constants";
import { ChangeType } from "./OTP";


export function customNavigation(navigation: StackNavigationProp<StackNavigationParam>){

    useFocusEffect(
        React.useCallback(() => {
            const onBackPress = () => {
                // @ts-ignore
                navigation.navigate("Card", {screen: "Settings"});
                return true; 
            };
        
            BackHandler.addEventListener("hardwareBackPress", onBackPress);
        
            return () => BackHandler.removeEventListener("hardwareBackPress", onBackPress);
            }, [navigation])
    );
}

export function changeCallbacks(navigation: StackNavigationProp<StackNavigationParam>, type: ChangeType){

    function getTitle() {
        switch(type){
            case 'email': return "Email Change";
            case 'delete': return "Account Deletion";
            case 'forgot': return "Password Reset";
            case 'password': return "Password Change";
            case 'username': return "Username Change";
        }
    }

    function getSuccessMsg() {
        switch(type){
            case 'email': return "Your email was successfully updated";
            case 'delete': return "Your account was successfully deleted";
            case 'password': 
            case 'forgot': return "Your password was successfully changed";
            case 'username': return "Your username was successfully updated";
        }
    }

    const success = () => {
        navigation.navigate("Login");

        Dialog.show({
            type: ALERT_TYPE.SUCCESS,
            title: getTitle(),
            button: 'Ok',
            textBody: getSuccessMsg(),
        });
    };


    const failure = (error: string[]) => {
        Dialog.show({
            type: ALERT_TYPE.DANGER,
            title: getTitle(),
            button: 'Ok',
            textBody: "Failed due to: " + error.join('\n'),
        });
    };

    const error = () => {
        Dialog.show({
            type: ALERT_TYPE.DANGER,
            title: getTitle(),
            button: 'Ok',
            textBody: DEFAULT_ERROR,
        });
    };

    return {success, failure, error};
}