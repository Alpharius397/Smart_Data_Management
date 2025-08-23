import React from "react";
import { Modal, View, ActivityIndicator, Text, StyleSheet } from "react-native";

type LoadingPopupProps = {
    visible: boolean;
    message?: string;
};

export default function Popup({ visible, message = "Loading..." }: LoadingPopupProps) {
    return (
        <Modal
        visible={visible}
        transparent
        animationType="fade"
        >
        <View style={styles.overlay}>
            <View style={styles.container}>
            <ActivityIndicator size="large" color="#4CAF50" />
            <Text style={styles.text}>{message}</Text>
            </View>
        </View>
        </Modal>
    );
}

const styles = StyleSheet.create({
    overlay: {
        flex: 1,
        backgroundColor: "rgba(0,0,0,0.4)",
        justifyContent: "center",
        alignItems: "center",
    },
    container: {
        backgroundColor: "white",
        padding: 20,
        borderRadius: 16,
        alignItems: "center",
        shadowColor: "#000",
        shadowOpacity: 0.2,
        shadowOffset: { width: 0, height: 2 },
        shadowRadius: 6,
        elevation: 5,
    },
    text: {
        marginTop: 12,
        fontSize: 16,
        fontWeight: "500",
        color: "#333",
    },
});