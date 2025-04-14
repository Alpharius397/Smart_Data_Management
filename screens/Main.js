import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, Button, Image, NativeEventEmitter, TouchableHighlight, Alert } from 'react-native';
import { createDrawerNavigator, DrawerItem, DrawerItemList } from '@react-navigation/drawer';
import { NavigationIndependentTree, NavigationContext } from '@react-navigation/native';
import {decrypt_data} from '../scripts/encryption';
import {generate_image} from '../scripts/image';
import { ScrollView } from 'react-native-gesture-handler';
import bad_image from '../scripts/bad_image';
import { NativeModules } from 'react-native';
import { beginPayment, generateOption } from '../razorpay/payment';
import Axios, { REFRESH, SUBSCRIBER } from '../http/axios';
import { getRefreshToken, removeAccessToken, removeRefreshToken, setAccessToken, setRefreshToken } from '../storage/storage';
import { showAlert } from '../utils/alert';

const { NfcModule } = NativeModules;

const Drawer = createDrawerNavigator();
const emitter = new NativeEventEmitter(NfcModule);

function get_column(jsonData){
  const {_, data} = jsonData;

  const IMAGE = /^Profile_Image$/;
  const SEM = /.+Sem_(\d+)$/;

  var profile_col = []
  var sem_col = []
  var personal_col = []

  Object.keys(data).forEach((col) => {
      if(IMAGE.test(col)){
        profile_col.push(col);
      }
      else if(SEM.test(col)){
        sem_col.push(col);
      }
      else{
        personal_col.push(col);
      }
  }); 

  var sem_dict = Object({});
  profile_col = profile_col[0];

  sem_col.forEach((col) =>{

    const sem = SEM.exec(col);

    if(!sem_dict.hasOwnProperty(sem[1])){
      sem_dict[sem[1]] = [];
    }

    sem_dict[sem[1]].push(col);

  });

  return {profile_col,sem_dict,personal_col};
}

const Logout = (navigation, message) => {

  async function __logout__() {
    try{
      await removeAccessToken();
      await removeRefreshToken();
    }
    catch(e){
      console.error(e)  
    }
    showAlert("Auth Status", message);
    navigation.navigate("Login");
  }

  __logout__().then().catch()
}

// Home Screen Component
function HomeScreen({ navigation }) {

  const [image,setImage] = useState(null);
  const [nfcData, setNfcData] = useState(null);
  const [column, setColumn] = useState(null);
  const [nfcSupport, setSupport] = useState(null);
  const [data, setData] = useState(true);
  const [sub, setSub] = useState(false);

  const eventType = "onNfcScan";

  async function checkNfcSupport() {
    try {
        const supported = await NfcModule.isSupported();
        console.log("NFC Supported:", supported);
        setSupport(supported);
    } catch (error) {
        console.error("Error checking NFC support:", error);
        setSupport(false);
    }
  }

  useEffect(() => {
    checkNfcSupport();
    isPub();
  }, []);

  function setListener(){
    emitter.addListener(eventType, (data) => {
      
      try{
        var res=data.replace(/[\u0000-\u001F]/g, '');
        console.log(res)
        msg = JSON.parse(res).msg;
        setNfcData(msg);
        scanning(msg);
        emitter.removeAllListeners(eventType);
      }
      catch(error){
        console.error("Listener Error: ", error)
      }

    })
    console.log("Event Attached")
  }

  function startNfcScan(){
    try {
      
      NfcModule.readyState().then(res => {console.log(res)}).catch(err => console.error(err));
      NfcModule.startNfcScan();
      setListener();
    } catch (error) {
      console.warn("NFC Error:", error);
    }
  };


  function scanning(Data){
    if(Data==null) return

      let nfcdata = decrypt_data(Data,"123456789123456789123456");
      console.log("JSON Data: ",nfcdata);

      try{
        let col = get_column(nfcdata);
        setData(nfcdata);
        setImage(generate_image(nfcdata.data[col.profile_col])||bad_image);
        setColumn(col);
      }
      catch(e){
        showAlert("NFC Card", "Data cannot be parsed")
      }
  }

  function HeaderRender(){
      return (
        <View style={styles.headerBox}>
          <Text style={styles.headerText}>
            {data.header.university} - {data.header.institute} - {data.header.branch}
          </Text>
        </View>
      );
  }
  
  function ImageRender(){

      return (
        <View style={styles.imageRow}>
          <Image
            source={{ uri: image }} style={styles.image} 
          />
      </View>
      );
  }

  function DataRender(){

      return (column.personal_col.map((row,index) => (
        <View style={styles.tableRow} key={index}>
          <Text style={styles.tableCell}>{row}</Text>
          <Text style={styles.tableCell}>{data.data[row]}</Text>
        </View>
      )));
  }

  function SemRender(){

    return (
      <View style={styles.semInfo}>
        <Text style={styles.semPart}>Semester Info</Text>
      <ScrollView contentContainerStyle={styles.scroll}>
      {Object.entries(column.sem_dict).map(([sem, subjects], index) => (
        <View key={index} style={styles.semTable}>
          <Text style={styles.semHead}>Semester {sem}</Text>
          <View key={index} style={styles.tableCol}>
            {subjects.map((sub, idx) => (
              <View key={idx} style={styles.tableRow}>
                <Text style={styles.tableCell}>{sub}</Text>
                <Text style={styles.tableCell}> {data.data[sub]}</Text>
              </View> 
            ))}
          </View>
        </View>
      ))}
    </ScrollView>
    </View>
  );


  }

  const NfcScanButton = () => {
    
    if(nfcSupport && sub){
      return (<Button onPress={startNfcScan} style={styles.button} title='Scan NFC Card' />)

    }
    else if(sub){
      return (<Text>This Device doesn't support NFC scanning or NFC scanning is not enabled</Text>)

    }
    else{
      return null;
    }
  }

  const PaymentScan = () => {
    
    return !sub ? (
        <Button onPress={() => beginPayment(generateOption(), paymentSuccess, paymentError)} style={styles.button} title='Payment' />
      ) : (
        null
      )
  }

  const completeView = () => {
    return (
      <ScrollView contentContainerStyle={styles.scroll}>
          <View style={styles.table}>
              {(data && data.header) ? HeaderRender() : null}
              {(image) ? ImageRender() : null}
              {(data && data.data && column && column.personal_col) ? DataRender() : null}
          </View>
          {(data && data.data && column && column.sem_dict) ? SemRender() : null}
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
          <PaymentScan/>
        </View>
      </ScrollView>
  );
  }


  const dataAvailable = () => {
    return data && data.header && data.data && column && column.personal_col && image;
  }
  /**
 * @param {string} order_id
 * @param {string} payment_id
 * @returns {void}
 */
function paymentSuccess(order_id, payment_id){
  let retry = true;

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
          showAlert("Login Failure", "Server Error Occurred")
        }
        else if(error.status==403){
          showAlert("Login Failure", "Unauthorized Entry")
        }
        else if(error.status==401 && retry){
          retry = false;
          
          const refresh = await getRefreshToken();

          if(refresh==null){
            Logout(navigation, 'Unauthorized Entry! Logging Out')
          }

          try{
            const retryAttempt = await Axios.post(REFRESH,{
              'refresh':refresh
            });

            const {token, status, error} = retryAttempt.data;

            if(token && status && error==null){
              await setAccessToken(token);
              await success();
            }
          }
          catch(error){
            console.warn(e);
          }
          Logout(navigation, 'Unauthorized Entry! Logging Out');
        }

        console.warn(e);

      }
    }

  }
  success();

}
/**
 * @param {{error: {code: string, description: string, source: string, step: string, reason: string, metadata: object}}} param
 * @returns {void}
 */
function paymentError(param){
  console.log("Received: " ,param.error)
  showAlert("Payment Failed", "Reason: "+param.error.reason+", By: "+param.error.source+", Step: "+param.error.step);
}

async function isPub(){
  try{
    const response = await Axios.get(SUBSCRIBER);
    const { status, error } = response.data;

    if(status && error==null){
      setSub(true);
    }
  }
  catch(e){
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
      <Image source={require('../assets/images/close.png')} style={styles.close_style}/>
      </TouchableHighlight>

      <View style={{flexDirection:'row', alignItems:'center'}}>
        <Image source={require('../assets/images/defaultUser.png')} style={styles.user_image} />
        <Text style={styles.userName}>{`Hello User,\n${userName}`}</Text>

      </View>


      <DrawerItemList {...props} />

      <DrawerItem 
            label="Log out"
            onPress={()=>{ Logout(props.navigation,"Logout Successfully"); }}
      />

    </View>
  );
}

// Main App Component
export default function App({navigation,route}) {
  return (
    <NavigationIndependentTree>
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
  scroll_h:{
    padding: 8,
    overflowY:'scroll',
    marginRight:8
  },
  scroll: {
      padding: 16,
      alignContent:'center',
      justifyContent:'center',
    },
    image: {
      width: 150,
      height: 150,
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
      borderBottomWidth: 1,
      borderLeftWidth:0,
      borderTopWidth: 1,
      borderColor: '#ccc',
      flexDirection: "row",
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
      minWidth:150,
      borderRightWidth: 1,
      borderBottomWidth:0,
      borderLeftWidth: 0,
      borderTopWidth: 0,
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
      marginTop:10,
      textAlign:'center',
      borderColor:'#ccc',
      borderWidth:1,
      marginBottom:10,
      marginLeft:10,
      marginRight:10
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