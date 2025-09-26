package com.Smart_NFC

import android.content.pm.PackageManager;
import android.app.Activity
import android.content.Intent
import com.facebook.react.bridge.Promise
import com.facebook.react.bridge.ReactApplicationContext
import com.facebook.react.bridge.ReactContextBaseJavaModule
import com.facebook.react.bridge.ReactMethod
import android.nfc.NfcAdapter;
import android.nfc.Tag;
import android.nfc.TagLostException;
import androidx.activity.ComponentActivity;
import java.security.NoSuchAlgorithmException
import java.util.Arrays
import java.util.Objects
import javax.crypto.Cipher
import javax.crypto.NoSuchPaddingException
import javax.crypto.spec.IvParameterSpec
import com.facebook.react.modules.core.DeviceEventManagerModule
import com.Smart_NFC.CardActionsLogicv2
import kotlin.text.replace
import kotlinx.serialization.*
import kotlinx.serialization.json.*
import expo.modules.kotlin.types.Either

sealed interface JsonSerializable

@Serializable
data class CardReadJson(var ok: Boolean, var data: String?, var uid: String?, var error: String?): JsonSerializable

@Serializable
data class Message(var ok: Boolean, var error: String?): JsonSerializable

class NfcModule(reactContext: ReactApplicationContext) : ReactContextBaseJavaModule(reactContext), NfcAdapter.ReaderCallback {

    private val stringBuilder = StringBuilder()
    private val json = Json { ignoreUnknownKeys = true }
    private var libInstance: NxpNfcLib? = null
    private var mCardLogic: CardActionsLogic? = null
    private var rCardLogic: CardActionsLogicv2? = null
    private var context = reactContext

    companion object {
        var mString: String? = ""
    }

    override fun getName(): String {
        return "NfcModule"
    }

    private fun hexToAscii(hexStr: String?): String {

        if( hexStr==null ) return ""

        var HexStr: String = hexStr

        if((HexStr.length % 2) == 1){
            HexStr = HexStr.slice(0..(HexStr.length-1))
        }

        val regex = Regex("^(.*?):([0-9A-F]+)$")
        var cleanString: String = HexStr.replace("\n", "").replace(" ", "")
        var Hex: String = regex.findAll(cleanString).map { it.groupValues[2] }.joinToString()
    
        return Hex.chunked(2).map { it.toInt(16).toChar() }.toString() 
    }
    
    internal inline fun <reified T: JsonSerializable> to_json(r: T): String {
        return Json.encodeToString(r)
    }

    @ReactMethod
    fun DESFireCheck(promise: Promise) {
        var message = Message(false, null)

        try{
            DESFireFactory.getInstance()
            message.ok = true
        }
        catch(e: Exception){
            message.error = e.toString()
        }

        promise.resolve(to_json<Message>(message))
    }

    @ReactMethod
    fun readyState(promise: Promise){
        var message = Message(false, null)

        try{
            mCardLogic = CardActionsLogic.getInstance() // initialize instance
            rCardLogic = CardActionsLogicv2.instance // initialize instance??
            initializeLibrary()
            initializeCipherinitVector()
            message.ok = true
        }
        catch(e: Exception){
            message.error = e.toString()
        }
        
        promise.resolve(to_json<Message>(message))
    }

    @ReactMethod
    fun isSupported(promise: Promise){
        try{
            val activity: Activity? = reactApplicationContext.currentActivity;
            if (activity?.getPackageManager()!!.hasSystemFeature(PackageManager.FEATURE_NFC)) {
                promise.resolve(true);
            }
        }
        catch(e: Exception){
            promise.resolve(false)
        }
    }

    @ReactMethod
    fun isEnabled(promise: Promise) {
        try{
            NfcAdapter.getDefaultAdapter(context);
            promise.resolve(true)
        }
        catch(e: Exception){
            promise.resolve(false)
        }
    }

    @ReactMethod
    fun startNfcScan() {
        val activity = getCurrentActivity()
        val nfcAdapter: NfcAdapter? = NfcAdapter.getDefaultAdapter(context)
        nfcAdapter?.enableReaderMode(activity, this, NfcAdapter.FLAG_READER_NFC_A or NfcAdapter.FLAG_READER_NFC_B, null)
    }

    @ReactMethod
    fun addListener(eventName: String) {
        // Keep: Required for RN built in Event Emitter Calls.
    }

    @ReactMethod
    fun removeListeners(count: Integer) {
        // Keep: Required for RN built in Event Emitter Calls.
    }

    @ReactMethod
    fun endNfcScan() {
        val activity = getCurrentActivity()
        val nfcAdapter: NfcAdapter? = NfcAdapter.getDefaultAdapter(context)
        nfcAdapter?.disableReaderMode(activity)
    }

    override fun onTagDiscovered(tag: Tag?) {
        if (tag == null) return  // Ensure the tag is not null

        var text: CardReadJson = cardLogic(tag)
        reactApplicationContext
            .getJSModule(DeviceEventManagerModule.RCTDeviceEventEmitter::class.java)
            .emit("onNfcScan", to_json<CardReadJson>(text))
    }

    private fun initializeCipherinitVector() {
        /* Initialize the Cipher */
        cipher = Cipher.getInstance("AES/CBC/NoPadding")
        /* set Application Master Key */
        bytesKey = KEY_APP_MASTER.toByteArray()

        /* Initialize init vector of 16 bytes with 0xCD. It could be anything */
        val ivSpec = ByteArray(16)
        Arrays.fill(ivSpec, 0xCD.toByte())
        iv = IvParameterSpec(ivSpec)
    }

    private fun initializeLibrary() {
        libInstance = NxpNfcLib.getInstance()
    }

    private fun cardLogic(tag: Tag): CardReadJson {
        val type = libInstance!!.getCardType(tag) //Get the type of the card
        val activity: ComponentActivity = getCurrentActivity()!! as ComponentActivity
        var res: CardReadJson = CardReadJson(false, null, null, null)

        if (type == CardType.UnknownCard) {
            res.error = "Unknown type of Card"
            return res
        }

        when (type) { // type = card type ( accepts only DESFireEV1 )
            CardType.DESFireEV1 -> try {
                
                res.data = hexToAscii(mCardLogic?.desfireEV1CardLogic(
                        activity,
                        DESFireFactory.getInstance().getDESFire( // important
                            libInstance!!.customModules
                        )
                    )
                )

                res.uid = hexToAscii(rCardLogic?.desfireEV1CardLogic(
                        activity,
                        DESFireFactory.getInstance().getDESFire( // important check
                            libInstance!!.customModules
                        )
                    )
                )

                res.ok = true
            } catch (t: Throwable) {
                res.error = t.toString()
                res.ok = false
            }

            else -> {
                res.error = "Unknown type of Card" // not reachable?
            }
        }

        return res
    }
}
