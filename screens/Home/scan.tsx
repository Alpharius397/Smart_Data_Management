import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, Button, Image,  ActivityIndicator, Animated, Easing, TouchableHighlight } from 'react-native';
import { createDrawerNavigator, DrawerItem, DrawerItemList } from '@react-navigation/drawer';
import generate_image from '../../scripts/image';
import { ScrollView } from 'react-native-gesture-handler';
import { beginPayment, generateOption } from '../../razorpay/payment';
import { showAlert } from '../../utils/alert';
import { CardJson, Dictionary } from '../../types/card';
import { HomeParam, LoadingParams } from '../../types/screens/Home';
import { ErrorJsonType } from '../../types/razorpay';
import data from './data';
import { useLoadingText, useNFC, usePage, usePurchaser, useScan } from '../../hooks/screens/Home';
import { HeaderType, RowData, SemData, SubjectData } from '../../types/Home';

const Drawer = createDrawerNavigator();

function HeaderRender({ university, institute, branch }: HeaderType){
    return (
        <View style={styles.headerBox}>
            <Text style={styles.headerText}>
                {university} - {institute} - {branch}
            </Text>
        </View>
    );
}

function ImageRender(images: Dictionary<string, string>){
    var imageData = new Array<RowData>;

    Object.keys(images).forEach((key) => {
        imageData.push({ column: key, value: images[key]});
    });

    return (
        imageData.map(({column, value}, _) => (
            (
                <View style={styles.imageRow}>
                    <Image
                        source={{ uri: generate_image(value) }} style={styles.image} 
                    />
                    <Text style={styles.imageRow}>{column}</Text>
                </View>
            )
        ))
    );
}

function PersonalRender(data: Dictionary<string, string>){

    var dataMap = new Array<RowData>();

    Object.keys(data).forEach((key) => {
        dataMap.push({ column:key, value:data[key] });
    });

    return (
            dataMap.map(({ column, value } , index) => (
                <View style={styles.tableRow} key={index + column}>
                    <Text style={styles.tablePersonal}>{column}</Text>
                    <Text style={styles.tablePersonal}>{value}</Text>
                </View>
                )
            )
    );
}

function SemRender(data: Dictionary<number, Dictionary<string, [string, string | number]>>){

    var semData = new Array<SemData>;

    Object.keys(data).forEach((key) => {
        let subjects = new Array<SubjectData>;
        Object.keys(data[key]).forEach((val) => {
            let a: [string, string | number] = data[key][val]
            subjects.push( { subject: val, value: a[0], maxValue: a[1] } );
        });
        semData.push({semester: key, subjects: subjects});
    })

    return (
        <View style={styles.semInfo}>
            <Text style={styles.semPart}>Semester Info</Text>
                <ScrollView contentContainerStyle={styles.scroll}>
                    {semData.map(({ semester, subjects}, index) => (
                        <View key={index + "Header"} style={styles.semTable}>
                            <Text style={styles.semHead}>Semester {semester}</Text>
                            <ScrollView contentContainerStyle={styles.scroll} horizontal={true}>
                            
                                <View key={index + "Cell"} style={styles.tableCol}>
                                    <View key={index + "Col"} style={styles.tableRow}>
                                        <Text style={styles.tableCell}> Subject Name </Text>
                                        <Text style={styles.tableCell}> Marks Obtained </Text>
                                        <Text style={styles.tableCell}> Max. Marks </Text>
                                    </View> 
                                    {subjects.map(({subject, value, maxValue }, idx) => (
                                        <View key={`${index}_${idx}`} style={styles.tableRow}>
                                            <Text style={{...styles.tableCell, textAlign: 'left'}}>{subject}</Text>
                                            <Text style={{...styles.tableCell, textAlign: 'left'}}> {value}</Text>
                                            <Text style={{...styles.tableCell, textAlign: 'left'}}> {maxValue}</Text>
                                        </View> 
                                    ))}
                                </View>
                            </ScrollView>
                        </View>
                    ))}
            </ScrollView>
        </View>
    );
}

function WaitingForNFC({ loadingText, children}: LoadingParams ){
    const pulseAnim = React.useRef(new Animated.Value(1)).current;

    useEffect(() => {
        Animated.loop(
            Animated.sequence([
            Animated.timing(pulseAnim, {
                toValue: 1.1,
                duration: 800,
                easing: Easing.inOut(Easing.ease),
            useNativeDriver: true,
            }),
            Animated.timing(pulseAnim, {
            toValue: 1,
            duration: 800,
            easing: Easing.inOut(Easing.ease),
            useNativeDriver: true,
            }),
        ])
        ).start();
    }, [pulseAnim]);

    return (
        <View style={waitStyles.container}>
            <Animated.View style={[waitStyles.circle, { transform: [{ scale: pulseAnim }] }]} />
            <Text style={waitStyles.text}> {loadingText} </Text>
            <ActivityIndicator size="large" color="#4A90E2" style={{marginBottom: 15}} />

            {children}
        </View>
    );
}

const waitStyles = StyleSheet.create({
    container: {
        flex: 1,
        alignItems: 'center',
        justifyContent: 'center',
        padding: 20,
    },
    text: {
        fontSize: 18,
        marginTop: 20,
        marginBottom: 10,
        color: '#333',
        fontWeight: '500',
    },
    circle: {
        width: 100,
        height: 100,
        borderRadius: 50,
        backgroundColor: '#4A90E2',
        opacity: 0.2,
        marginBottom: 30,
    },
});

export function ScanScreen() {

    const [isScanning, isPurchasing, setScanning, setPurchasing] = usePage(true);
    const [nfcData, setNfcData] = useState<CardJson | null>(null);
    const nfcSupport = useNFC();
    const [loadingState, cardFoundCallBack, validityCallBack, decryptCallBack] = useLoadingText();
    const [isScanningNFC, startScan, endScan] = useScan(okCallBack, errorCallBack, paymentNeeded, timeoutCallback, cardFoundCallBack, validityCallBack, decryptCallBack);
    const [isLoading, purchaseCard] = usePurchaser();

    function timeoutCallback() {
        showAlert("NFC Scan", "NFC Scan Timeout. Please try again!");
    }

    function okCallBack(data: CardJson){
        setNfcData(data);
    }

    function errorCallBack(error: string){
        showAlert("NFC Scan", `NFC Scan Failed! ${error}`);
    }

    function paymentNeeded(message: string){
        showAlert("Payment Needed", message);
        setPurchasing();
    }

    const NfcScanButton = () => {

        if(isScanningNFC){
            return (
            <WaitingForNFC loadingText={loadingState}>
                <Button onPress={endScan} title='End Scan' />
            </WaitingForNFC>
            )

        } else if(nfcSupport && (!isScanningNFC)){
            return (
                <Button onPress={scanState} title='Scan NFC Card' />
            );
        } else {
            return (<Text>This Device doesn't support NFC scanning or NFC scanning is not enabled</Text>)
        }
    }

    const PaymentScan = () => {        
            //@ts-expect-error
            return (<Button onPress={() => beginPayment(generateOption(), paymentSuccess, paymentError)} title='Payment' />)
    }

    const TableView = () => {
        return (
            <ScrollView contentContainerStyle={styles.scroll}>

                <View style={styles.table}>
                    {(
                        nfcData && 
                        nfcData.university && 
                        nfcData.institute && 
                        nfcData.branch
                    ) ? HeaderRender({ university: nfcData.university, institute: nfcData.institute, branch: nfcData.branch  }) : null}

                    {(nfcData && nfcData.images) ? ImageRender(nfcData.images) : null}
                    {(nfcData && nfcData.personal) ? PersonalRender(nfcData.personal) : null}
                </View>

                {(nfcData && nfcData.sem_data) ? SemRender(nfcData.sem_data) : null}

            </ScrollView>
        );
    }

    function scanState(){
        setNfcData(null);
        startScan();
    }

    const NfcScan = () => {
        return (
            <View style={styles.buttonWrapper}>
                <NfcScanButton/>
            </View>
        );
    }

    const Payment = () => {
        return (
            <View style={styles.buttonWrapper}>
                <PaymentScan/>
            </View>
        );
    }

    function paymentSuccess(cardID:string, order_id: string, payment_id: string){
        const paymentOk = () => {
            showAlert("Payment Status", "Payment Successful! Please re-scan the card");
            setScanning()
        } 

        const paymentFailed = (error: string) => {
            showAlert("Payment Status", "Payment Unsuccessful! "+error);

        }
        
        const paymentError = (error: string) => {
            showAlert("Payment Status", "Failed to send Payment Status! "+error);
        }

        purchaseCard(cardID, order_id, payment_id, paymentOk, paymentFailed, paymentError);
    }

    function paymentError(error_data: ErrorJsonType){
        showAlert("Payment Failed", `Payment Failed, Reason: ${error_data.reason}, By: ${error_data.source}, Step: ${error_data.step}`);
    }

    return (
        <ScrollView contentContainerStyle={styles.centeredContainer}>
            {
                (nfcData !== null) && TableView()
            }
            {
                (isScanning === true) && NfcScan()
            }
            {
                (isPurchasing === true) && Payment()
            }
        </ScrollView>
    )

}

// Styles
const styles = StyleSheet.create({
    container: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
    },
    title: {
        fontSize: 24,
        fontWeight: 'bold',
    },
    userSection: {
        marginVertical: 20,
    },
    userName: {
        fontSize: 18,
        fontWeight: '600',
    },
    drawerContent: {
        marginTop: 30,
    },
    scroll: {
        padding: 8,
        alignContent:'center',
        justifyContent:'center',
    },
    image: {
        width: 100,
        height: 100,
        marginBottom: 16,
        margin:5
    },
    table: {
        borderWidth: 1,
        borderColor: '#ccc',
        borderRadius: 4,
        overflow: 'hidden',
    },
    tableRow: {
        flex:1,
        flexDirection:'row',
        borderColor: '#ccc',
        alignItems: "stretch",
        textAlign: "left",
        justifyContent: "flex-start",
    },
    tableRowFirst: {
        flex:1,
        flexDirection:'row',
        borderColor: '#ccc',
        alignItems: "stretch",
        justifyContent: "space-around",
    },
    tableRowLast:{
        borderBottomWidth:0
    },
    tableCol:{
        flexDirection:'column',
    },
    tableCell: {
        flex: 1,
        padding: 10,
        maxWidth:200,
        minWidth:200,
        borderRightWidth: 1,
        borderLeftWidth: 1,
        borderTopWidth: 1,
        borderBottomWidth: 1,
        borderColor: '#ccc',
        textAlign: 'center',
        textAlignVertical:'center',
    },
    tablePersonal: {
        flex: 1,
        padding: 10,
        maxWidth:200,
        borderRightWidth: 1,
        borderLeftWidth: 1,
        borderTopWidth: 1,
        borderBottomWidth: 1,
        borderColor: '#ccc',
        textAlign: 'center',
        textAlignVertical:'center',
    },
    tableCellLast: {
        borderRightWidth: 0,
    },
    imageRow:{
        display:'flex',
        margin:'auto',
        borderColor:'#ccc',
        marginTop:5,
        alignContent:'center',
        justifyContent:'center',
    },
    close_style:{
        width:20,
        height:20,
        cursor:'pointer'
    },
    user_image:{
        width:50,
        height:50,
        margin:10
    },
    button:{
        marginTop:20,
        width:80,
        height:40
    },
    headerBox:{
        display:'flex',
        backgroundColor:'lightblue',
    },
    headerText:{
        color:'white',
        fontWeight:'bold',
        fontSize:18,
        textAlign:'center'
    },
    semTable:{
        textAlign:'center',
        borderColor:'#ccc',
        borderWidth:1,
        margin:0,
        marginBottom: 8
    },
    semHead:{
        textAlign:'center',
        textAlignVertical:'center',
        marginBottom:8,
        marginTop:8
    },
    semInfo:{
        marginTop:10,
        marginBottom:10,
        borderColor:'#ccc',
        borderWidth:1
    },
    semPart:{
        backgroundColor:'lightblue',
        padding:8,
        textAlign:'center',
        color:'white',
        fontWeight:'bold',
    },
    centeredContainer: {
        flexGrow: 1,
        justifyContent: 'center',
        alignItems: 'center',
        padding: 16,
    },
    
    buttonWrapper: {
        alignItems: 'center',
        width:500
    },
    
});





