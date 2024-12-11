import React, { useState } from 'react';
import { View, Text, StyleSheet, Button, Image, Icon, TouchableHighlight } from 'react-native';
import { createDrawerNavigator } from '@react-navigation/drawer';
import { NavigationContainer,NavigationIndependentTree } from '@react-navigation/native';
import sample_data from '../scripts/text';
import {decrypt_data} from '../scripts/encryption';
import {generate_image} from '../scripts/image';
import { ScrollView } from 'react-native-gesture-handler';
const Drawer = createDrawerNavigator();

// Home Screen Component
function HomeScreen() {

  const [image,setImage] = useState('');
  const data = decrypt_data(sample_data,"123456789123456789");
  generate_image(data.IMAGE).then((res) => {setImage(res)});

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
        {dataLoad(data).map((row, index) => (
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
function CustomDrawerContent(props) {
  const userName = "Aryan Mandke"; // Replace with dynamic user data if needed

  const closeDrawer = () => {props.navigation.closeDrawer()}

  return (
    <View style={{ flex: 1, padding: 20 }}>
      {/* User Name Section */}
      <TouchableHighlight onPress={closeDrawer} style={styles.close_style}>
      <Image source={require('../../../assets/images/close.png')} style={styles.close_style}/>
      </TouchableHighlight>
      <View style={styles.userSection}>
        <Text style={styles.userName}>Hello, {userName}</Text>
      </View>

      {/* Other Drawer Items */}
      <View style={styles.drawerContent}>
        <Button
          title="Logout"
          color="#d9534f"
          onPress={() => {
            alert('You have been logged out!'); // Replace with your logout logic
            // props.navigation.navigate("Login");
            props.navigation.closeDrawer();
          }}
        />
      </View>
    </View>
  );
}

// Main App Component
export default function App() {
  return (
    <NavigationIndependentTree>
      <Drawer.Navigator
        drawerContent={(props) => <CustomDrawerContent {...props} />}
      >
        <Drawer.Screen name="Home" component={HomeScreen} />
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
    }
});
