import React from 'react';
import { View, Text, Image, StyleSheet, TouchableOpacity, RefreshControl } from 'react-native';
import { StackParam } from '../../zod/screens';
import { removeAccessToken, removeRefreshToken } from '../../storage';
import ShimmerPlaceholder from 'react-native-shimmer-placeholder';
import LinearGradient from 'react-native-linear-gradient';
import { ScrollView } from 'react-native-gesture-handler';
import { useProfile } from '../../hooks/screens/Settings/Profile';
import {ALERT_TYPE, Dialog, Toast} from 'react-native-alert-notification';

export default function SettingsScreen ({ navigation }: StackParam) {
    
    const {profileData, refetch, isLoading}= useProfile();

    const goToUsername = () => {
        Dialog.show({
            type: ALERT_TYPE.WARNING,
            title: 'Username Change',
            button: 'Proceed',
            textBody: "Are you sure about this?",
            onPressButton: () => { navigation.navigate("Username")}
        });
    };

    const goToEmail = () => {
        Dialog.show({
            type: ALERT_TYPE.WARNING,
            title: 'Email Change',
            button: 'Proceed',
            textBody: "Are you sure about this?",
            onPressButton: () => { navigation.navigate("Email")}
        });
    };

    const goToPassword = () => {
        Dialog.show({
            type: ALERT_TYPE.WARNING,
            title: 'Password Change',
            button: 'Proceed',
            textBody: "Are you sure about this?",
            onPressButton: () => { navigation.navigate("Password")}
        });
    };

    const goToDelete = () => {
        Dialog.show({
            type: ALERT_TYPE.WARNING,
            title: 'Account Deletion Change',
            button: 'Proceed',
            textBody: "Are you sure about this?",
            onPressButton: () => { navigation.navigate("Delete")}
        });
    };

    const handleLogout = () => {
        Dialog.show({
            type: ALERT_TYPE.WARNING,
            title: 'Logout Request',
            button: 'Proceed',
            textBody: "Are you sure about this?",
            onPressButton: () => {
                Dialog.hide();
                removeAccessToken();
                removeRefreshToken();
                navigation.navigate("Login");
                Toast.show({
                    type: ALERT_TYPE.SUCCESS,
                    title: 'Authentication Status',
                    autoClose: 1000,
                    textBody: 'Logout Successful'
                });      
            }
        });

    };

    return (
        <ScrollView style={styles.container} refreshControl={
            <RefreshControl refreshing={false} onRefresh={refetch} />
        }>

            <View style={styles.profileContainer}>
            <ShimmerPlaceholder
                    visible={!isLoading}
                    style={styles.usernamePlaceholder}
                    shimmerStyle={styles.usernamePlaceholder}
                    LinearGradient={LinearGradient}
                >
                <Text style={{...styles.email, marginBottom: 10}}> Student at {profileData.university} - {profileData.institute} - {profileData.branch}</Text>
            </ShimmerPlaceholder>
                <Image source={require("../../assets/images/default.profile.png")} style={styles.profileImage} />
                <ShimmerPlaceholder
                    visible={!isLoading}
                    style={styles.usernamePlaceholder}
                    shimmerStyle={styles.usernamePlaceholder}
                    LinearGradient={LinearGradient}
                >
                    <Text style={styles.username}>{ profileData.username }</Text>
                    <Text style={styles.email}>{ profileData.email }</Text>
                </ShimmerPlaceholder>
            </View>

            <TouchableOpacity style={styles.optionItem} onPress={goToUsername}>
                <Text style={styles.optionText}>Change Username</Text>
            </TouchableOpacity>


            <TouchableOpacity style={styles.optionItem} onPress={goToEmail}>
                <Text style={styles.optionText}>Change Email</Text>
            </TouchableOpacity>

            
            <TouchableOpacity style={styles.optionItem} onPress={goToPassword}>
                <Text style={styles.optionText}>Change Password</Text>
            </TouchableOpacity>

            <TouchableOpacity style={styles.optionItem} onPress={goToDelete}>
                <Text style={{...styles.optionText, color: 'red', fontWeight: 'bold'}}>Delete Account</Text>
            </TouchableOpacity>

            <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
                <Text style={styles.logoutText}>Log Out</Text>
            </TouchableOpacity>
        </ScrollView>
    );
};


const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#fff',
        padding: 20,
        paddingTop: 0,
    },
    profileContainer: {
        alignItems: 'center',
        marginVertical: 30,
        marginTop: 10,
    },
    profileImage: {
        width: 100,
        height: 100,
        borderRadius: 50,
        backgroundColor: '#ccc',
    },
    usernamePlaceholder: {
        margin: 0,
        marginTop: 5,
        marginBottom: 5,
        borderRadius: 4,
    },
    username: {
        margin: 'auto',
        fontSize: 20,
        fontWeight: 'bold',
    },
    optionList: {
        marginTop: 10,
    },
    optionItem: {
        paddingVertical: 15,
        borderBottomWidth: 1,
        borderColor: '#ddd',
    },
    optionText: {
        fontSize: 16, 
    },
        logoutButton: {
        marginTop: 40,
        paddingVertical: 15,
        backgroundColor: '#e74c3c',
        borderRadius: 8,
        alignItems: 'center',
    },
    logoutText: {
        color: '#fff',
        fontSize: 16,
        fontWeight: '600',
    },
    email: {
        fontSize: 14,
        color: '#666',
        margin: 'auto',
        marginTop: 2,
        width: 'auto'
    },
});