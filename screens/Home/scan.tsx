import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, Button, Image,  ActivityIndicator, Animated, Easing, TouchableHighlight } from 'react-native';
import { createDrawerNavigator, DrawerItem, DrawerItemList } from '@react-navigation/drawer';
import generate_image from '../../scripts/image';
import { ScrollView } from 'react-native-gesture-handler';
import { beginPayment, generateOption } from '../../razorpay/payment';
import Axios, { SUBSCRIBER } from '../../axios';
import { removeAccessToken, removeRefreshToken } from '../../storage';
import { showAlert } from '../../utils/alert';
import { isAxiosError } from 'axios';
import { CardJson, Dictionary } from '../../types/card';
import { HomeNavigator, HomeParam } from '../../types/screens/Home';
import { isSupported, isEnabled, removeListener, setListener, startNfcScan } from '../../utils/NfcModule';
import { OptionJson, SuccessCallback, CheckoutJson, CheckoutError, ErrorJsonType } from '../../types/razorpay';
import { NavigationIndependentTree } from '@react-navigation/native';
import data from './data';

const Drawer = createDrawerNavigator();
const NFC_SCAN_DURATION: number = 1000 * 60; // 1 minute

//////////// TYPES ////////////
type JsTypesString = 'number' | 'string' | 'object'

type JsTypes = number | string | object | null

type HeaderType = {
    university: string,
    institute: string,
    branch: string,
}

type RowData = {
    column: string,
    value: string
}

type SubjectData = {
    subject: string
    value: string
    maxValue: string | number
}

type SemData = {
    semester: string,
    subjects: Array<SubjectData>
}


function check_value(obj: JsTypes, type: string[]): boolean {
    try{
        return type.find((x) => x === typeof(obj)) !== undefined;
    } catch(error) {
        return false;
    }
}

function check_object(obj: object, type_list: JsTypesString[][]): boolean {
    if(type_list.length === 0) return true;
    
    try{
        var res = true;

        if(typeof(obj) !== 'object'){
            res = res && check_value(obj, type_list[0]);
        } else {
            Object.keys(obj).forEach((key) => {
                res = res && check_value(key, type_list[0]) && check_object(obj[key], type_list.slice(1,));
            });
        }
        return res;
    }
    catch(error) {
        return false;
    }
}

function check_format(jsonData: CardJson): boolean {

    try {
        const { university, institute, branch, images, sem_data, personal } = jsonData;

        if(!(
            check_value(university, ["string"]) &&
            check_value(institute, ["string"]) &&
            check_value(branch, ["string"]) &&
            check_object(images, [["string"], ["string"]]) &&
            check_object(personal, [["string"], ["string"]]) &&
            check_object(sem_data, [["string"], ["string"], ["string"], ["string", "number"]])
        )){
            throw new Error("Invalid Format")
        }

        return true;

    }
    catch {
        return false;
    }

}

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
        imageData.map(({column, value}, idx) => (
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
            <View style={styles.tableRow} key={index}>
                <Text style={styles.tableCell}>{column}</Text>
                <Text style={styles.tableCell}>{value}</Text>
            </View>
            ))
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
                        <View key={index} style={styles.semTable}>
                            <Text style={styles.semHead}>Semester {semester}</Text>
                            <ScrollView contentContainerStyle={styles.scroll} horizontal={true}>
                            
                                <View key={index} style={styles.tableCol}>
                                    <View key={"it's me mario"} style={styles.tableRow}>
                                        <Text style={styles.tableCell}> Subject Name </Text>
                                        <Text style={styles.tableCell}> Marks Obtained </Text>
                                        <Text style={styles.tableCell}> Max. Marks </Text>
                                    </View> 
                                    {subjects.map(({subject, value, maxValue }, idx) => (
                                        <View key={idx} style={styles.tableRow}>
                                            <Text style={styles.tableCell}>{subject}</Text>
                                            <Text style={styles.tableCell}> {value}</Text>
                                            <Text style={styles.tableCell}> {maxValue}</Text>
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

function HomeScreen({ navigation }: HomeParam) {

    const [nfcData, setNfcData] = useState<CardJson | null>(null);
    const [nfcSupport, setSupport] = useState<boolean>(false);
    const [scan, setScan] = useState<boolean>(false);
    const [cardStatus, setCardStatus] = useState<boolean | null>(null);
    const [sub, setSub] = useState<boolean>(null);
    var scanTimer: NodeJS.Timeout | null = null;

    async function checkNfcSupport() {
        try {
            const supported = await isSupported();
            console.log("NFC Supported:", supported);
            setSupport(supported);
        } catch (error) {
            console.error("Error checking NFC support:", error);
            setSupport(false);
        }
    }

    useEffect(() => {
        checkNfcSupport(); // check for support
    }, []);

    useEffect(() => {

        if(scan === true ){
            startNfcScan();
            setListener(onSuccessScan);

            scanTimer = setTimeout(() => {
                onTimeout(); // cleaning up your mess
            }, NFC_SCAN_DURATION);

        } else {
            removeListener();
        }

        return () => {
            clearTimeout(scanTimer);
        }

    }, [scan]);

    function onTimeout() {
        removeListener();
        setScan(false);
        showAlert("NFC Scan", "NFC Scan Timeout. Please try again!");
    }


    function onSuccessScan(data: CardJson | null){

        if(data == null ){
            setCardStatus(false); // card scan failed
        } else {
            if(check_format(data)){
                setNfcData(data);
                setScan(false);
                setCardStatus(true);
            } else {
                setCardStatus(false);
            }
        }
    }

    function beginScan(){
        setScan(true);
    };

    function endScan(){
        setScan(false);
    }

    const NfcScanButton = () => {

        if(scan){
            return (<><WaitingForNFC/><Button onPress={endScan} title='End Scan' /></>)
        } else if(nfcSupport){
            return (
                <Button onPress={beginScan} title='Scan NFC Card' />
            );
        } else {
            return (<Text>This Device doesn't support NFC scanning or NFC scanning is not enabled</Text>)
        }
    }

    const PaymentScan = () => {
        
        if( sub === true ){
            return null;
        } else {
            //@ts-expect-error
            return (<Button onPress={() => beginPayment(generateOption(), paymentSuccess, paymentError)} title='Payment' />)
        }
    }

    const completeView = () => {
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
                <NfcScanButton/>
                <PaymentScan/>

            </ScrollView>
        );
    }


    const initialView = () => {
        return (
            <ScrollView contentContainerStyle={styles.centeredContainer}>
                <View style={styles.buttonWrapper}>
                    <NfcScanButton/>
                </View>
            </ScrollView>
        );
    }


    const dataAvailable = () => {
        return check_format(nfcData);
    }

    function paymentSuccess(order_id: string, payment_id: string){

        async function success() {

            try{
                const response = await Axios.put(SUBSCRIBER, 
                    {
                    order_id: order_id,
                    payment_id: payment_id
                    }
                )

                const { status, error } = response.data;

                if(status){
                    showAlert("Payment Success", (error==null)?"Payment was successful":error)
                    setSub(true);
                }
            }
            catch(error){
                if(isAxiosError(error)){

                    if(error.status==409){
                        showAlert("Payment Status", error.response.data.error)
                    }
                    else if(error.status==500){
                        showAlert("Payment Status", "Server Error Occurred")
                    }
                    else if(error.status==422){
                        showAlert("Payment Status", "Payment was unsuccessful")
                    }
                    else if(error.status==401){
                        
                    }
                    else if(error.status==403){
                        showAlert("Payment Status", error.response.data.error)
                    }

                console.warn(error);

                }
            }

        }
    
        success();

    }

    function paymentError(error_data: ErrorJsonType){
        showAlert(`Payment Failed, Reason: ${error_data.reason}, By: ${error_data.source}, Step: ${error_data.step}`,"");
    }

    async function isPub(){
        try{
            const response = await Axios.get(SUBSCRIBER);
            const { status, error } = response.data;

            if(status && error==null){
                setSub(true);
            }
        } catch(e){
            console.warn(e);
        }
    }

    return (dataAvailable()?completeView():initialView());

}

// Custom Drawer Content Component
function CustomDrawerContent({props,params}) {

    const userName = params.user;
    const closeDrawer = () => {props.navigation.closeDrawer()}

    return (
        <View style={{ flex: 1, padding: 20 }}>
        <TouchableHighlight onPress={closeDrawer} style={styles.close_style}>
        <Image source={require('../../assets/images/close.png')} style={styles.close_style}/>
        </TouchableHighlight>

        <View style={{flexDirection:'row', alignItems:'center'}}>
            <Image source={require('../../assets/images/default.profile.png')} style={styles.user_image} />
            <Text style={styles.userName}>{`Hello User,\n${userName}`}</Text>

        </View>


        <DrawerItemList {...props} />

        {/* <DrawerItem 
                label="Log out"
                onPress={()=>{ Logout(props.navigation,"Logout Successfully"); }}
        /> */}

        </View>
    );
}

// Main App Component
export default function App({navigation,route}) {
    return (
        <NavigationIndependentTree>
        {/**@ts-ignore*/}
        <Drawer.Navigator
            drawerContent={(props) => <CustomDrawerContent props={{...props}} params={route.params} />}
        >
            <Drawer.Screen name="Home" children={(props) => <HomeScreen navigation={navigation} />} props options={{drawerItemStyle: {marginBottom:10}}}/>
        </Drawer.Navigator>
        </NavigationIndependentTree>
    );
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


const WaitingForNFC = () => {
const pulseAnim = React.useRef(new Animated.Value(1)).current;

React.useEffect(() => {
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
    <View style={styles.container}>
      <Animated.View style={[styles.circle, { transform: [{ scale: pulseAnim }] }]} />
      <Text style={styles.text}>Waiting for NFC card...</Text>
      <ActivityIndicator size="large" color="#4A90E2" />
    </View>
  );
};

const waitStyles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f4f6f8',
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
