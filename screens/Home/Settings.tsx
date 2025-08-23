import React from 'react';
import { View, Text, Image, StyleSheet, TouchableOpacity, FlatList, RefreshControl } from 'react-native';
import { removeAccessToken, removeRefreshToken } from '../../storage';
import ShimmerPlaceholder from 'react-native-shimmer-placeholder';
import LinearGradient from 'react-native-linear-gradient';
import { ScrollView } from 'react-native-gesture-handler';
import { useProfile } from '../../hooks/screens/Settings/Profile';
import { StackParam } from '../../zod/screens';

const options = [
    { id: '1', title: 'Change Username' },
    { id: '2', title: 'Change Email' },
    { id: '3', title: 'Change Password' },
    { id: '4', title: 'Delete Account' },
];

export default function SettingsScreen ({ navigation }: StackParam ) {
    
    const {profileData, refetch, isLoading}= useProfile();


    const handleOptionPress = (optionTitle: string) => {
        console.log(`Pressed: ${optionTitle}`);
        // Navigate or handle accordingly
    };

    const handleLogout = () => {
        removeAccessToken();
        removeRefreshToken();
        navigation.navigate("Login");
    };

    return (
        <ScrollView style={styles.container} refreshControl={
            <RefreshControl refreshing={false} onRefresh={refetch} />
        }>

        <View style={styles.profileContainer}>
            <Text style={{...styles.email, marginBottom: 10}}> Student at {profileData.university} - {profileData.institute} - {profileData.branch}</Text>
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

        {/* Options List */}
        <FlatList
            data={options}
            keyExtractor={(item) => item.id}
            renderItem={({ item }) => (
            <TouchableOpacity style={styles.optionItem} onPress={() => handleOptionPress(item.title)}>
                <Text style={styles.optionText}>{item.title}</Text>
            </TouchableOpacity>
            )}
            contentContainerStyle={styles.optionList}
        />

        {/* Logout Button */}
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
    },
    profileContainer: {
        alignItems: 'center',
        marginVertical: 30,
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