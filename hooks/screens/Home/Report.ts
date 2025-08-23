import * as FileSystem from "expo-file-system";
import * as Linking from "expo-linking";
import * as Sharing from "expo-sharing";
import { getAccessToken, getRefreshToken } from "../../../storage";
import * as IntentLauncher from "expo-intent-launcher";
import { Platform } from "react-native";

export function useReport(uri: string) {

    const downloadPDF = async () => {
        try {
            const fileName = "Report.pdf";
            const fileUri = FileSystem.documentDirectory + fileName;
            const token = await getAccessToken(); 
            const refresh = await getRefreshToken(); 
            const downloadObject = FileSystem.createDownloadResumable(
                uri,
                fileUri,
                {
                    headers:{
                        Authorization:`Bearer ${token}`,
                        Refresh:`Bearer ${refresh}`,
                    }
                },
            );

            const response = await downloadObject.downloadAsync();

            if (response?.status === 200) {
                await openPDF(fileUri);
            }
        } catch (error) {
            console.error("Error downloading the PDF: ", error);
        }
    };

    const openPDF = async (fileUri: string) => {
        try {
            const contentUri = await FileSystem.getContentUriAsync(fileUri);
            console.log("Content URI: ", contentUri);

            if (Platform.OS !== 'android') {
                // Prefer native PDF viewer
                if (await Linking.canOpenURL(contentUri)) {
                    Linking.openURL(contentUri);
                } else {
                    await Sharing.shareAsync(contentUri, { UTI: "com.adobe.pdf" });
                }
            } else {
                IntentLauncher.startActivityAsync("android.intent.action.VIEW", {
                    data: contentUri,
                    flags: 1,
                });
            }
        } catch(error) {
            console.error("Error opening the PDF: ", error);
        }
    };

    return downloadPDF;
}
