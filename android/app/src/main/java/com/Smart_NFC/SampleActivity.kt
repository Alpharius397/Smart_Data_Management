package com.Smart_NFC

import com.facebook.react.bridge.Promise
import com.facebook.react.bridge.ReactApplicationContext
import com.facebook.react.bridge.ReactContextBaseJavaModule
import com.facebook.react.bridge.ReactMethod

// Replace 'MyJarClass' with the actual class from your .jar file
// import com.example.myjar.MyJarClass

class MyNativeModule(reactContext: ReactApplicationContext) : ReactContextBaseJavaModule(reactContext) {

    override fun getName(): String {
        return "MyNativeModule"
    }

    @ReactMethod
    fun myNativeMethod(input: String, promise: Promise) {
        try {
            // Call the method from your JAR file.
            val result: String = "Okay"
            promise.resolve(result)
        } catch (e: Exception) {
            promise.reject("ERROR", e)
        }
    }
}
