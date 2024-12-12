import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, Button, Image, Icon, TouchableHighlight, Alert } from 'react-native';
import { createDrawerNavigator, DrawerItem, DrawerItemList } from '@react-navigation/drawer';
import { NavigationContainer,NavigationIndependentTree } from '@react-navigation/native';
import sample_data from '../scripts/text';
import {decrypt_data} from '../scripts/encryption';
import {generate_image} from '../scripts/image';
import { ScrollView } from 'react-native-gesture-handler';
const Drawer = createDrawerNavigator();

// Home Screen Component
function HomeScreen() {

  const [image,setImage] = useState('');
  const [data,setData] = useState([]);

  useEffect(()=>{
    let data = decrypt_data(sample_data,"123456789123456789");
    setData(dataLoad(data));
    generate_image(data.IMAGE).then((res) => {setImage(res)});

  },[]);

  function dataLoad(jsonObject) {
    let tableData = [];
    Object.keys(jsonObject).forEach((key) => {
      if (key !== 'IMAGE') {
        tableData.push({ key: key, value: jsonObject[key] });
      }
    });
    return tableData;
  }

  return (
    <ScrollView contentContainerStyle={styles.scroll}>
      <View style={styles.table}>
        <View style={styles.imageRow}>
          <Image source={{ uri: image }} style={styles.image} />
          </View>
        {data.map((row, index) => (
          <View style={styles.tableRow} key={index}>
            <Text style={styles.tableCell}>{row.key}</Text>
            <Text style={styles.tableCell}>{row.value}</Text>
          </View>
        ))}
      </View>
    </ScrollView>
  );
}

// Custom Drawer Content Component
function CustomDrawerContent({props,params}) {

  const userName = params.user;
  const closeDrawer = () => {props.navigation.closeDrawer()}

  return (
    <View style={{ flex: 1, padding: 20 }}>
      {/* User Name Section */}
      <TouchableHighlight onPress={closeDrawer} style={styles.close_style}>
      <Image source={require('../../../assets/images/close.png')} style={styles.close_style}/>
      </TouchableHighlight>

      <View style={{flexDirection:'row', alignItems:'center'}}>
        <Image source={require('../../../assets/images/defaultUser.png')} style={styles.user_image} />
        <Text style={styles.userName}> {`Hello User,\n ${userName}`} </Text>
      </View>


      <DrawerItemList {...props} />
    </View>
  );
}

function Logout({navigation}){
  navigation.navigate("Login");
  Alert.alert("Logout", "Logout Successfully",[{text: 'Ok',style: 'cancel'}],{cancelable: true});

  return (<View></View>);

}

// Main App Component
export default function App({navigation,route}) {
  return (
    <NavigationIndependentTree>
      <Drawer.Navigator
        drawerContent={(props) => <CustomDrawerContent props={{...props}} params={route.params} />}
      >
        <Drawer.Screen name="Home" component={HomeScreen} options={{drawerItemStyle: {marginBottom:10}}}/>
        <Drawer.Screen name="Logout" component={Logout} />
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
      padding: 16,
    },
    image: {
      width: 200,
      height: 200,
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
      flexDirection: 'row',
      borderBottomWidth: 1,
      borderTopWidth: 1,
      borderColor: '#ccc',
    },
    tableCell: {
      flex: 1,
      padding: 8,
      borderRightWidth: 1,
      borderColor: '#ccc',
      textAlign: 'center',
    },
    tableCellLast: {
      borderRightWidth: 0,
    },
    imageRow:{
      display:'flex',
      margin:'auto',
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
    }
});
