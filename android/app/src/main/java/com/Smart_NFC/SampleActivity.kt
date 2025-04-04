package com.Smart_NFC

import android.content.pm.PackageManager;
import android.app.Activity
import android.content.Intent
import com.facebook.react.bridge.Promise
import com.facebook.react.bridge.ReactApplicationContext
import com.facebook.react.bridge.ReactContextBaseJavaModule
import com.facebook.react.bridge.ReactMethod
import com.nxp.nfclib.CardType
import com.nxp.nfclib.KeyType
import com.nxp.nfclib.NxpNfcLib
import com.nxp.nfclib.desfire.DESFireFactory
import com.nxp.nfclib.exceptions.NxpNfcLibException
import com.nxp.nfclib.interfaces.IKeyData
import android.nfc.NfcAdapter;
import android.nfc.Tag;
import android.nfc.TagLostException;
import androidx.activity.ComponentActivity;
import com.tinkertechlogix.smartcard.nfcsmartcertilibrary.Constants.ALIAS_DEFAULT_FF
import com.tinkertechlogix.smartcard.nfcsmartcertilibrary.Constants.ALIAS_KEY_3KTDES
import com.tinkertechlogix.smartcard.nfcsmartcertilibrary.Constants.EXTRA_KEYS_STORED_FLAG
import com.tinkertechlogix.smartcard.nfcsmartcertilibrary.Constants.KEY_APP_MASTER
import com.tinkertechlogix.smartcard.nfcsmartcertilibrary.Constants.PRINT
import com.tinkertechlogix.smartcard.nfcsmartcertilibrary.Constants.TOAST
import com.tinkertechlogix.smartcard.nfcsmartcertilibrary.Constants.TOAST_PRINT
import com.tinkertechlogix.smartcard.nfcsmartcertilibrary.Constants.bytesKey
import com.tinkertechlogix.smartcard.nfcsmartcertilibrary.Constants.cipher
import com.tinkertechlogix.smartcard.nfcsmartcertilibrary.Constants.default_ff_key
import com.tinkertechlogix.smartcard.nfcsmartcertilibrary.Constants.iv
import com.tinkertechlogix.smartcard.nfcsmartcertilibrary.Constants.packageKey
import com.tinkertechlogix.smartcard.nfcsmartcertilibrary.CardActionsLogic // check this
import java.security.NoSuchAlgorithmException
import java.util.Arrays
import java.util.Objects
import javax.crypto.Cipher
import javax.crypto.NoSuchPaddingException
import javax.crypto.spec.IvParameterSpec
import com.facebook.react.modules.core.DeviceEventManagerModule

data class Result(var ok: Boolean, var msg: String?, var module: String)

class MyNativeModule(reactContext: ReactApplicationContext) : ReactContextBaseJavaModule(reactContext), NfcAdapter.ReaderCallback {

    private val stringBuilder = StringBuilder()
    private var libInstance: NxpNfcLib? = null
    private var mCardLogic: CardActionsLogic? = null
    private var context = reactContext
    companion object {
        var mString: String? = ""
    }

    override fun getName(): String {
        return "MyNativeModule"
    }

    private fun JSON(r: Result): String{
        return "{\"ok\":${r.ok}, \"msg\":\"${r.msg}\", \"module\":\"${r.module}\"}"
    }

    @ReactMethod
    fun ___DESFireCheck(promise: Promise) {
        try{
            val a = DESFireFactory.getInstance()
            promise.resolve(JSON(Result(true, "okay", "DESFIRE")))

            // promise.resolve(a.toString())
        }
        catch(e: Exception){
            promise.resolve(JSON(Result(false, e.toString(), "DESFIRE")))
        }
    }

    @ReactMethod
    fun readyState(promise: Promise){
        try{
            mCardLogic = CardActionsLogic.getInstance() // initialize instance
            initializeLibrary()
            initializeCipherinitVector()
            promise.resolve(JSON(Result(true, "okay", "readyState")))
        }
        catch(e: Exception){
            promise.resolve(JSON(Result(false, e.toString(), "readyState")))
        }
    }

    // @ReactMethod
    // fun onIntent(promise: Promise){
    //         try{
    //             val activity: Activity? = getCurrentActivity();

    //             if(activity == null){
    //                 throw Exception("Failed to get activity")
    //             }
    //             val intent: Intent = activity.intent
    //             promise.resolve(JSON(processIntent(intent)))
    //         }
    //         catch(e: Exception){
    //             promise.resolve(JSON(Result(false, e.toString(), "onIntent")))
    //         }
    // }
    
    // fun processIntent(intent: Intent): Result {
    //     stringBuilder.delete(0, stringBuilder.length)
    //     val extras = intent.extras
    //     extras?.let {
    //         mString = it.getString("android.nfc.extra.TAG")
    //     } ?: run {
    //         mString = "" // Default value in case extras is null or the key does not exist
    //     }

    //     return cardLogic(intent)

    // }

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
    fun endNfcScan() {
        val activity = getCurrentActivity()
        val nfcAdapter: NfcAdapter? = NfcAdapter.getDefaultAdapter(context)
        nfcAdapter?.disableReaderMode(activity)
    }

    override fun onTagDiscovered(tag: Tag?) {
        if (tag == null) return  // Ensure the tag is not null
            var text: Result = cardLogic(tag)
            reactApplicationContext
                .getJSModule(DeviceEventManagerModule.RCTDeviceEventEmitter::class.java)
                .emit("onNfcScan", JSON(text))
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

    private fun cardLogic(tag: Tag): Result {
        val type = libInstance!!.getCardType(tag) //Get the type of the card
        val activity: ComponentActivity = getCurrentActivity()!! as ComponentActivity
        var res: Result = Result(false, null, "cardLogic")

        if (type == CardType.UnknownCard) {
            res.msg = "Unknown Card"
            return res
        }

        when (type) { // type = card type (accepts only DESFireEV1 )
            CardType.DESFireEV1 -> try {
                
                res.msg = mCardLogic?.desfireEV1CardLogic(
                        activity,
                        DESFireFactory.getInstance().getDESFire( // important
                            libInstance!!.customModules
                        )
                    )

                res.ok = true
            } catch (t: Throwable) {
                res.msg = t.toString()
                res.ok = false
            }

            else -> {
                res.msg = "Unknown type of Card"
            }
        }

        return res
    }
}