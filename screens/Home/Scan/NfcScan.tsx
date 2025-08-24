import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, Image,  ActivityIndicator, Animated, Easing, TouchableHighlight, Button, RefreshControl } from 'react-native';
import generate_image from '../../../scripts/image';
import { ScrollView } from 'react-native-gesture-handler';
import { useLoadingText } from '../../../hooks/screens/Home/Purchase';
import { CardProtoType, HeaderProtoType, ImageArray, ImageProtoType, PersonalArray, PersonalProtoType, SemesterData, SemesterProtoType, SubjectArray} from '../../../zod/screens/Home/Scan';
import { useHeader, useNFC, useScan } from '../../../hooks/screens/Home/Scan';
import { LoadingParams } from '../../../zod/screens/Home/Card';
import ShimmerPlaceholder from 'react-native-shimmer-placeholder';
import LinearGradient from 'react-native-linear-gradient';
import { useCard } from './context';
import { URL } from '../../../axios';
import { useReport } from '../../../hooks/screens/Home/Report';
import {ALERT_TYPE, Dialog, Toast} from 'react-native-alert-notification';

function LoadingScreen({ loadingText, children}: LoadingParams ){
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
        fontSize: 20,
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

function HeaderRender({ university, institute, branch }: HeaderProtoType){

    const {transform, isError, isLoading} = useHeader({ university, institute, branch })
    
    if(isError){
        Toast.show({
            type: ALERT_TYPE.WARNING,
            title: "Heading Fetch",
            textBody: "Failed to fetch Header Details",
        });
    }         

    return (
        <View style={styles.headerBox}>

            <ShimmerPlaceholder
                visible={!isLoading}
                style={styles.placeholder}
                shimmerStyle={styles.placeholder}
                LinearGradient={LinearGradient}
            >
                <Text style={styles.headerText}>
                    {transform.university} - {transform.institute} - {transform.branch}
                </Text>
            </ShimmerPlaceholder>
        </View>
    );
}

function ImageRender({images}: {images: ImageProtoType}){

    let imageArray = new Array<ImageArray>();

    Object.keys(images).forEach((key) => {
        let value = images[key];
        imageArray.push({column: key, value: value});
    })

    return (
        imageArray.map(({column, value}) => (
            (
                <View style={styles.imageRow}>
                    <Image
                        source={{ uri: generate_image(value)}} style={styles.image} key={`${column}-image`}
                    />
                    <Text style={styles.imageRow}>{column}</Text>
                </View>
            )
        ))
    );
}

function PersonalRender({personal}: {personal: PersonalProtoType}){

    let personalArray = new Array<PersonalArray>();

    Object.keys(personal).forEach((key) => {
        let value = personal[key];
        personalArray.push({ column: key, value: value});
    })

    return (
        personalArray.map(({ column, value } , index) => (
            <View style={styles.tableRow} key={`${column}-personal-${index}`}>
                <Text style={styles.tablePersonal}>{column}</Text>
                <Text style={styles.tablePersonal}>{value}</Text>
            </View>
            )
        )
    );
}

export default function ScanScreen({ switchPurchase }: {switchPurchase: () => void}) {

    const [nfcData, setNfcData] = useState<CardProtoType | null>(null);
    const nfcSupport = useNFC();
    const [loadingState, cardFoundCallBack, validityCallBack, decryptCallBack] = useLoadingText();
    const [isScanningNFC, startScan, endScan] = useScan(okCallBack, errorCallBack, paymentNeeded, timeoutCallback, cardFoundCallBack, validityCallBack, decryptCallBack);
    const { setCard, card } = useCard();
    const [cardID, setCardID] = useState<string>(null);


    function timeoutCallback() {
        Dialog.show({
            type: ALERT_TYPE.INFO,
            title: "NFC Scan",
            button: 'Ok',
            textBody: "NFC Scan Timeout. Please try again!",
        });
    }

    function okCallBack(data: CardProtoType, uid: string){
        endScan();
        setNfcData(data);
        setCardID(uid);
    }

    function errorCallBack(error: string){
        Dialog.show({
            type: ALERT_TYPE.WARNING,
            title: "NFC Scan",
            button: 'Ok',
            textBody: `NFC Scan Failed! ${error}`,
        });
    }

    function paymentNeeded(cardID: string, message: string){
        Dialog.show({
            type: ALERT_TYPE.INFO,
            title: "Payment Needed",
            button: 'Proceed',
            textBody: message,
            onPressButton: () => {
                Dialog.hide();
                setCard(cardID)
                switchPurchase();
            }
        });
    }

    const NfcScanButton = () => {
        
        if(isScanningNFC){
            return (
            <LoadingScreen loadingText={loadingState}>
                <TouchableHighlight onPress={endScan}>
                    <Text style={styles.scanButton}>
                        End Scan
                    </Text>
                </TouchableHighlight>
            </LoadingScreen>
            )

        } else if(nfcSupport && (!isScanningNFC)){
            return (
                <View style={styles.horizontal}>
                    <TouchableHighlight onPress={scanState} style={{margin: 5}}>
                        <Text style={styles.scanButton}>
                            Scan Document
                        </Text>
                    </TouchableHighlight>

                    {(nfcData !== null) && (cardID !== null) && (
                        <TouchableHighlight onPress={useReport(URL.REPORT(cardID, null))} style={{margin: 5}}>
                            <Text style={styles.fullDownButton}>
                                Download Full Report
                            </Text>
                        </TouchableHighlight>
                    )}
                </View>

            );
        } else {
            return (
                <View>
                    <Image source={require('../../../assets/images/no.nfc.png')} style={styles.imageNoNfc}/>
                    <Text style={{padding: 10, textAlign: 'justify', fontSize: 18, fontWeight: 'bold'}}>
                        This Device doesn't support NFC scanning!
                    </Text>
                </View>
            );
        }
    }

    
    function SemRender({semester}: {semester: SemesterProtoType}){
    
        var semData = new Array<SemesterData>();
        
        var columns: Map<string, Array<string>> = new Map();
    
        Object.keys(semester).forEach((sem) => {
            let subs = semester[sem]
            let cols = new Array<string>();
            let subArray = new Array<SubjectArray>();
    
            Object.keys(subs.subject).forEach((name) => {
                let meta = subs.subject[name]
                Object.keys(meta.other).forEach((extra) => {
                    // Save extra columns for each sems
                    if (!cols.includes(extra)) cols.push(extra);
                });
    
                subArray.push({ name: name, meta: meta})
    
            });
    
            semData.push({semester: sem, subjects: subArray});
    
            columns.set(sem, cols);
        });
    
        const Capitalize = (str: any) => {
            let a = String(str);
            return a.charAt(0).toUpperCase() + a.slice(1,);
        }
    
        const SubjectTable = ({sem, subjects, columns}: {sem: string, subjects: SubjectArray, columns: Map<string, Array<string>>}) => (
        
                <View style={styles.tableRow}>
                <Text style={{...styles.tableCell, textAlign: 'left'}}>{subjects.meta.id}</Text>
                <Text style={{...styles.tableCell, textAlign: 'left'}}>{subjects.name}</Text>
    
                {
                    (columns.has(sem)) && columns.get(sem).map((key, index) => (
                            <Text style={{...styles.tableCell, textAlign: 'left'}} key={`${index}-${key}-${sem}`}> 
                                {(subjects.meta.other[key] !== undefined) ? subjects.meta.other[key]:"-"} 
                            </Text>
                        )
                    )
                }
    
                <Text style={{...styles.tableCell, textAlign: 'left'}}> {subjects.meta.total}</Text>
            </View> 
        )
    
        const SubjectHeading = ({sem, columns}: {sem: string, columns: Map<string, Array<string>>}) => (
            <View style={styles.tableRow}>
                <Text style={styles.tableCell}>Subject Code</Text>
                <Text style={styles.tableCell}>Subject Name</Text>
                {
                    columns.has(sem) && columns.get(sem).map((cols, index) => (
                            <Text style={styles.tableCell} key={index}>{Capitalize(cols)}</Text>
                        )
                    )
                }
                <Text style={styles.tableCell}>Max. Marks</Text>
        </View> 
        )
    
        return (
            <View style={styles.semInfo}>
                <Text style={styles.semPart}>Semester Report</Text>
                    <ScrollView contentContainerStyle={styles.scroll}>
                        {semData.map(({ semester, subjects}, index) => (
                            <View key={index + "Header"} style={styles.semTable}>
                                <Text style={styles.semHead}>Semester {semester}</Text>
                                <ScrollView contentContainerStyle={styles.scroll} horizontal={true}>
                                
                                    <View key={index + "Cell"} style={styles.tableCol}>
                                        <SubjectHeading sem={semester} columns={columns} />
    
                                        {subjects.map((sub) => (
                                            <SubjectTable sem={semester} columns={columns} subjects={sub} />
                                        ))}
    
                                    </View>
                                </ScrollView>
                                <TouchableHighlight onPress={useReport(URL.REPORT(cardID, semester))} style={{margin: 5}}>
                                <Text style={styles.downButton}>
                                    Download Semester {semester} Report
                                </Text>
                            </TouchableHighlight>
                            </View>
                        ))}
                </ScrollView>
            </View>
        );
    }

    function scanState(){
        setNfcData(prev => null);
        startScan();
    }

    useEffect(() => {
        setNfcData(null);
    }, [card])


    const TableView = () => {

        if(nfcData === null){
            return;
        }

        return (
            <ScrollView contentContainerStyle={styles.scroll} refreshControl={<RefreshControl onRefresh={scanState} refreshing={false}></RefreshControl>}>

                <View style={styles.table}>
                    <HeaderRender university={nfcData.header.university} institute={nfcData.header.institute} branch={nfcData.header.branch} />
                    <ImageRender images={nfcData.image} />
                    <PersonalRender personal={nfcData.personal} />
                </View>

                <SemRender semester={nfcData.semester} />

            </ScrollView>
        );
    }



    return (
        <>
            <TableView />

            <View style={styles.buttonWrapper}>
                <NfcScanButton/>
            </View>
            
        </>
    )

}

// Styles
const styles = StyleSheet.create({
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
    imageRow:{
        display:'flex',
        margin:'auto',
        borderColor:'#ccc',
        marginTop:5,
        alignContent:'center',
        justifyContent:'center',
    },

    headerBox:{
        display:'flex',
        backgroundColor:'#1565C0',
        justifyContent: 'center',
        alignItems: 'center',
        padding: 5,
    },
    headerText:{
        color:'white',
        fontWeight:'bold',
        fontSize:18,
        textAlign:'center',
        textAlignVertical: 'center',
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
        marginTop:8,
        fontWeight: '900',
        fontSize: 16
    },
    semInfo:{
        marginTop:10,
        marginBottom:10,
        borderColor:'#ccc',
        borderWidth:1
    },
    semPart:{
        backgroundColor:'#1565C0',
        padding:8,
        textAlign:'center',
        color:'white',
        fontWeight:'bold',
        fontSize:18,
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
    scanButton: {
        backgroundColor: '#4A90E2',
        borderRadius: 5,
        padding: 10,
        color: 'white',
        fontWeight: 'bold',
        fontSize: 18,
        textAlign: 'center'
    },
    downButton: {
        backgroundColor: '#FF9800',
        borderRadius: 5,
        padding: 10,
        color: 'white',
        fontWeight: 'bold',
        fontSize: 16,
        textAlign: 'center'
    },
    fullDownButton: {
        backgroundColor: '#28A745',
        borderRadius: 5,
        padding: 10,
        color: 'white',
        fontWeight: 'bold',
        fontSize: 16,
        textAlign: 'center'
    },
    imageNoNfc: {
        width: 300,
        height: 300,
        margin: 'auto',
    },
    placeholder: {
        margin: 0,
        borderRadius: 4,
        color: 'grey'
    },
    horizontal: {
        flex: 1,
        flexDirection: 'row',
        justifyContent:'space-around'
    }
});





