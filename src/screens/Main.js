import React from 'react';
import { View, Text, StyleSheet, Button } from 'react-native';
import { createDrawerNavigator } from '@react-navigation/drawer';
import { NavigationContainer } from '@react-navigation/native';

const Drawer = createDrawerNavigator();

// A sample home screen
function HomeScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Welcome to the Home Screen!</Text>
    </View>
  );
}

// Custom drawer content
function CustomDrawerContent(props) {
  const userName = "Aryan Mandke"; // Replace with dynamic user data if needed

  return (
    <View style={{ flex: 1, padding: 20 }}>
      {/* User Name Section */}
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
            props.navigation.closeDrawer();
          }}
        />
      </View>
    </View>
  );
}

export default function App() {
  return (
      <Drawer.Navigator
        drawerContent={(props) => <CustomDrawerContent {...props} />}
      >
        <Drawer.Screen name="Home" component={HomeScreen} />
      </Drawer.Navigator>
  );
}

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
});
