import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, Button, Image, Icon, NativeEventEmitter , TouchableOpacity, TouchableHighlight, Alert } from 'react-native';
import { createDrawerNavigator, DrawerItem, DrawerItemList } from '@react-navigation/drawer';
import { NavigationContainer,NavigationIndependentTree } from '@react-navigation/native';
import sample_data from '../scripts/sample/encrypt';
import {decrypt_data} from '../scripts/encryption';
import {generate_image} from '../scripts/image';
import { ScrollView } from 'react-native-gesture-handler';
import NfcManager, {Ndef, NfcTech, NfcEvents} from 'react-native-nfc-manager';
import bad_image from '../scripts/sample/bad_image';
import { NativeModules } from 'react-native';
const { MyNativeModule } = NativeModules;

const Drawer = createDrawerNavigator();
const emitter = new NativeEventEmitter(MyNativeModule);

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




// async function scanNfcCard() {
//     try {
//         const cardData = await NfcManager.scanCard();
//         console.log("NFC Card Data:", cardData);
//         scanning(cardData); // Process scanned data
//     } catch (error) {
//         console.error("NFC Scan Error:", error);
//         showAlert('NFC Scan Error: ' + error.message);
//     }
// }


// Home Screen Component
function HomeScreen() {

  const [image,setImage] = useState(null);
  const [data,setData] = useState(null);
  const [nfcData, setNfcData] = useState(null);
  const [column, setColumn] = useState(null);
  const [nfcSupport, setSupport] = useState(true);

  const showAlert = (msg,action) => Alert.alert(msg,action,[{text: 'Ok',style: 'cancel',},],{cancelable: true},);

  NativeModules.MyNativeModule.readyState().then(res => {console.log(res)}).catch(err => console.error(err));
  NativeModules.MyNativeModule.onIntent().then(res => {console.log(res)}).catch(err => console.error(err));

  async function checkNfcSupport() {
    try {
        // const supported = await NfcModule.isNfcSupported();
        console.log("NFC Supported:", supported);
        setSupport(supported);
    } catch (error) {
        console.error("Error checking NFC support:", error);
        setSupport(false);
    }
}

  // useEffect(() => {
  //   if (!NfcModule || !NfcModule.scanCard) {
  //       console.error("❌ NFC Module is not linked properly!");
  //   } else {
  //       console.log("✅ NFC Module Loaded Successfully!");
  //   }

  //   checkNfcSupport();
  // }, []);

  async function scanNfcCard() {
    try {
        console.log("Starting NFC Scan...");
        // const cardData = await NfcModule.scanCard();
        NativeModules.MyNativeModule.onIntent().then(res => {console.log(res)}).catch(err => console.error(err));

        // console.log("NFC Card Data:", cardData);

        // // Process scanned NFC data
        // let decryptedData = decrypt_data(cardData, "123456789123456789123456");
        // let col = get_column(decryptedData);
        // setData(decryptedData);
        // setColumn(col);
        // setImage(generate_image(decryptedData.data[col.profile_col]) || bad_image);

    } catch (error) {
        console.error("NFC Scan Error:", error.message);
        showAlert('NFC Scan Error: ' + error.message);
    }
}




  function startNfcListener(){
    scanning(sample_data);
    console.warn('Listening');
    NfcManager.setEventListener(NfcEvents.DiscoverTag, get_msg);
  };

//   async function startNfcListener() {
//     try {
//         console.warn('Listening for DESFire EV1 card...');
//         await NfcManager.requestTechnology(NfcTech.IsoDep);

//         const tag = await NfcManager.getTag();
//         console.warn('DESFire EV1 Tag Found:', tag);

//         let cmd = [0x90, 0x60, 0x00, 0x00, 0x00]; // APDU command to select master application
//         let response = await NfcManager.transceive(cmd);

//         if (response[response.length - 1] !== 0x00) {
//             throw new Error('Authentication failed!');
//         }

//         console.warn('Authentication successful');

//         // APDU command to read data from file 0x01 (Modify based on your card structure)
//         let readCmd = [0x90, 0xBD, 0x00, 0x00, 0x00];
//         let readResponse = await NfcManager.transceive(readCmd);

//         if (readResponse[readResponse.length - 1] !== 0x00) {
//             throw new Error('Failed to read data from DESFire card!');
//         }

//         // Remove status byte from response
//         let encryptedData = readResponse.slice(0, -1);
        
//         console.warn('Raw Data:', encryptedData);

//         // Decrypt the received data using your function
//         let nfcdata = decrypt_data(encryptedData, "123456789123456789123456");

//         // Process data
//         let col = get_column(nfcdata);
//         setData(nfcdata);
//         setColumn(col);
//         setImage(generate_image(nfcdata.data[col.profile_col]) || bad_image);
        
//     } catch (error) {
//         console.error('NFC Error:', error);
//         showAlert('NFC Error: ' + error.message);
//     } finally {
//         await NfcManager.cancelTechnologyRequest();
//     }
// }


  function decode_msg(tag){
    const msg_all = tag.ndefMessage;

    if(msg && msg.length>0){
      const msg = msg_all[0];

      if (Ndef.isType(msg, Ndef.TNF_WELL_KNOWN, Ndef.RTD_TEXT)) {
        return Ndef.text.decodePayload(msg.payload);
      }
    }

    return null;
  }

  function get_msg(tag){
    console.warn('Tag found');
    const msg = decode_msg(tag);
    NfcManager.unregisterTagEvent().catch(()=>0);

    if(msg){
      scanning(msg);
    }
  }


  function scanning(sample_data){
      let nfcdata = decrypt_data(sample_data,"123456789123456789123456");
      let col = get_column(nfcdata);
      setData(nfcdata);
      setColumn(col);
      setImage(generate_image(nfcdata.data[col.profile_col])||bad_image);
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
      <ScrollView style={styles.scroll_h}>
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


  return (
    <ScrollView contentContainerStyle={styles.scroll}>
        <View style={styles.table}>
            {(data && data.header) ? HeaderRender() : null}
            {(image) ? ImageRender() : null}
            {(data && data.data && column && column.personal_col) ? DataRender() : null}
        </View>
        {(data && data.data && column && column.sem_dict) ? SemRender() : null}

        {nfcSupport ? (
            <Button onPress={scanNfcCard} style={styles.button} title='Scan NFC Card' />
        ) : (
            <Text>This Device doesn't support NFC scanning</Text>
        )}
    </ScrollView>
);
}


// Custom Drawer Content Component
function CustomDrawerContent({props,params}) {

  const userName = params.user;
  const closeDrawer = () => {props.navigation.closeDrawer()}
  const logout = () => {Alert.alert("Logout", "Logout Successfully",[{text: 'Ok',style: 'cancel'}],{cancelable: true});props.navigation.navigate("Login")}

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
            onPress={()=>{ logout(); }}
      />

    </View>
  );
}


// Initialize NFC on app launch

const NfcReader = () => {
  const [tagData, setTagData] = useState(null);
  const [nfc, setNfcData] = useState(null);
  
  
  useEffect(()=>{
    emitter.addListener('onNfcScan', (data) => {
      
      setNfcData(data);
      console.log(data);
      MyNativeModule.endNfcScan()
    })
    console.log("event attached")
    
  }, [])
  // Function to read NFC tag
  const readNfcTag = async () => {
    try {
      
      MyNativeModule.readyState().then(res => {console.log(res)}).catch(err => console.error(err));
      MyNativeModule.startNfcScan()
      // Request NFC tech (NDEF)
      
      // Read the tag
    } catch (error) {
      console.warn("NFC Error:", error);
    } finally {
      // Stop NFC detection
    }
  };

  console.log("NFC Event: ",nfc)

  return (
    <View style={{ flex: 1, justifyContent: "center", alignItems: "center" }}>
      <Text style={{ fontSize: 20, marginBottom: 20 }}>NFC Reader</Text>

      <TouchableOpacity
        onPress={readNfcTag}
        style={{
          backgroundColor: "#007AFF",
          padding: 15,
          borderRadius: 10,
        }}
      >
        <Text style={{ color: "#fff", fontSize: 18 }}>Scan NFC</Text>
      </TouchableOpacity>

      {tagData && (
        <View style={{ marginTop: 20 }}>
          <Text>NFC Tag Data:</Text>
          <Text>{JSON.stringify(tagData, null, 2)}</Text>
        </View>
      )}
    </View>
  );
};



// Main App Component
export default function App({navigation,route}) {
  return (
    <NavigationIndependentTree>
      <Drawer.Navigator
        drawerContent={(props) => <CustomDrawerContent props={{...props}} params={route.params} />}
      >
        <Drawer.Screen name="Home" component={NfcReader} options={{drawerItemStyle: {marginBottom:10}}}/>
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
    textAlign: 'center',
  },
  drawerContent: {
    marginTop: 30,
  },
  scroll: {
    padding: 16,
    alignContent: 'center',
    justifyContent: 'center',
  },
  image: {
    width: 120,  // Adjusted size for better mobile display
    height: 120,
    borderRadius: 8,
    marginBottom: 16,
  },
  tableContainer: {
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 4,
    padding: 10,
    alignItems: 'center', // Ensure proper alignment
  },
  tableRow: {
    flexDirection: 'row',
    flexWrap: 'wrap', // Wrap content to fit small screens
    justifyContent: 'space-between',
    borderBottomWidth: 1,
    borderColor: '#ccc',
    paddingVertical: 5,
  },
  tableCol: {
    flexDirection: 'column',
  },
  tableCell: {
    flex: 1,
    padding: 8,
    borderBottomWidth: 1,
    borderColor: '#ccc',
    textAlign: 'center',
    fontSize: 14, // Slightly smaller font for mobile
  },
  imageRow: {
    alignItems: 'center',
    marginTop: 10,
  },
  close_style: {
    width: 20,
    height: 20,
  },
  user_image: {
    width: 50,
    height: 50,
    margin: 10,
  },
  button: {
    marginTop: 20,
    width: 100,
    height: 45,
  },
  headerBox: {
    backgroundColor: 'lightblue',
    padding: 10,
    borderRadius: 5,
    marginBottom: 10,
  },
  headerText: {
    color: 'white',
    fontWeight: 'bold',
    fontSize: 16,
    textAlign: 'center',
  },
  semTable: {
    marginTop: 10,
    borderColor: '#ccc',
    borderWidth: 1,
    marginBottom: 10,
    borderRadius: 5,
    padding: 10,
  },
  semHead: {
    textAlign: 'center',
    fontWeight: 'bold',
    marginBottom: 5,
  },
  semInfo: {
    marginTop: 10,
    marginBottom: 10,
    borderColor: '#ccc',
    borderWidth: 1,
    padding: 10,
  },
  semPart: {
    backgroundColor: 'lightblue',
    padding: 8,
    textAlign: 'center',
    color: 'white',
    fontWeight: 'bold',
    borderRadius: 5,
  },
});