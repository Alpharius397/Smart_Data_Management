import React from 'react';
import { View, Text, TextInput, Button, StyleSheet } from 'react-native';
import { useForm, Controller } from 'react-hook-form';
import { useItems, useRegister } from '../hooks/screens/Register';
import { DEFAULT_ERROR } from '../constants';
import { Picker } from '@react-native-picker/picker';
import { registerSchema, RegisterFormData } from '../zod/screens/Register';
import { zodResolver } from '@hookform/resolvers/zod';
import Popup from '.';
import { StackParam } from '../zod/screens';
import { ALERT_TYPE, Dialog } from 'react-native-alert-notification';

export default function Register({ navigation }: StackParam) {

    const { control, handleSubmit, watch, formState: { errors, isValid } } = useForm<RegisterFormData>({
        resolver: zodResolver(registerSchema),
        mode: "onChange",
        defaultValues: {
            username: "",
            email: "",
            password: "",
            confirm_password: "",
            university: -1,
            institute: -1,
            branch: -1,
        }
    });

    const success = () => {
        navigation.navigate("Login");

        Dialog.show({
            type: ALERT_TYPE.SUCCESS,
            title: "Register Process",
            button: 'Ok',
            textBody: "Registration was successful!",
        });
    };


    const failure = (error: string[]) => {
        Dialog.show({
            type: ALERT_TYPE.DANGER,
            title: "Register Process",
            button: 'Ok',
            textBody: "Failed due to: " + error.join('\n'),
        });
    };

    const error = () => {
        Dialog.show({
            type: ALERT_TYPE.DANGER,
            title: "Register Process",
            button: 'Ok',
            textBody: DEFAULT_ERROR,
        });
    };

    const [submit, isPending] = useRegister(success, failure, error);

    const onSubmit = (data: RegisterFormData) => {
        submit({ data: data, validator: registerSchema });
    }

    // Hooks for fetching dropdown data
    const getUniversity = useItems("university");
    const getInstitute = useItems("institute", watch("university"));
    const getBranch = useItems("branch", watch("institute"));

    return (
        <View style={styles.container}>
            <Text style={styles.title}>Register</Text>
            <Popup visible={isPending} />

            <Controller
                control={control}
                name="username"
                rules={{ required: "Username is required" }}
                render={({ field: { onChange, value } }) => (
                    <TextInput
                        style={styles.input}
                        placeholder="Username"
                        value={value}
                        onChangeText={onChange}
                    />
                )}
            />
            {errors.username && <Text style={styles.error}>{errors.username.message}</Text>}

            <Controller
                control={control}
                name="email"
                render={({ field: { onChange, value } }) => (
                    <TextInput
                        style={styles.input}
                        placeholder="Email"
                        value={value}
                        onChangeText={onChange}
                        keyboardType="email-address"
                    />
                )}
            />
            {errors.email && <Text style={styles.error}>{errors.email.message}</Text>}

            <Controller
                control={control}
                name="password"
                rules={{ required: "Password is required", minLength: { value: 6, message: "Min 6 chars" } }}
                render={({ field: { onChange, value } }) => (
                    <TextInput
                        style={styles.input}
                        placeholder="Password"
                        value={value}
                        onChangeText={onChange}
                        secureTextEntry
                    />
                )}
            />
            {errors.password && <Text style={styles.error}>{errors.password.message}</Text>}

            <Controller
                control={control}
                name="confirm_password"
                render={({ field: { onChange, value } }) => (
                    <TextInput
                        style={styles.input}
                        placeholder="Confirm Password"
                        value={value}
                        onChangeText={onChange}
                        secureTextEntry
                    />
                )}
            />
            {errors.confirm_password && <Text style={styles.error}>{errors.confirm_password.message}</Text>}

            <Controller
                control={control}
                name="university"
                render={({ field: { onChange, value } }) => (
                    <View style={styles.pickerContainer}>

                        <Picker
                            placeholder="University"
                            selectedValue={value}
                            onValueChange={(itemValue, itemIndex) =>
                                onChange(itemValue)
                            }>
                            <Picker.Item label='Choose an University from below' value={-1} enabled={false} style={styles.pickLabel} key={-1} />

                            {
                                getUniversity.map((value) => (
                                    <Picker.Item label={value.name} value={value.id} key={value.id} style={styles.label} />
                                ))
                            }

                        </Picker>
                    </View>

                )}
            />
            <Controller
                control={control}
                name="institute"
                render={({ field: { onChange, value } }) => (
                    <View style={styles.pickerContainer}>
                        <Picker
                            placeholder="Institute"
                            selectedValue={value}
                            onValueChange={(itemValue, itemIndex) =>
                                onChange(itemValue)
                            }>
                            <Picker.Item label={'Choose an Institute from below'} value={-1} enabled={false} style={styles.pickLabel} key={-1} />

                            {
                                getInstitute.map((value, index) => (
                                    <Picker.Item label={value.name} value={value.id} key={value.id} style={styles.label} />
                                ))
                            }

                        </Picker>
                    </View>
                )}
            />
            <Controller
                control={control}
                name="branch"
                render={({ field: { onChange, value } }) => (
                    <View style={styles.pickerContainer}>
                        <Picker
                            placeholder="Branch"
                            selectedValue={value}
                            selectionColor={'red'}
                            onValueChange={(itemValue, itemIndex) =>
                                onChange(itemValue)
                            }>
                            <Picker.Item label='Choose a Branch from below' value={-1} enabled={false} style={styles.pickLabel} key={-1} />
                            {
                                getBranch.map((value) => (
                                    <Picker.Item label={value.name} value={value.id} key={value.id} style={styles.label} />
                                ))
                            }

                        </Picker>
                    </View>

                )}
            />
            <Button title="Register" onPress={handleSubmit(onSubmit)} disabled={!isValid} />

            <Text style={styles.link} onPress={() => navigation.navigate("Login")}>
                Already have an account? Login
            </Text>
        </View>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1, justifyContent: 'center', padding: 16 },
    title: { fontSize: 24, fontWeight: 'bold', marginBottom: 20, textAlign: 'center' },
    input: { borderWidth: 1, padding: 10, marginBottom: 10, borderRadius: 5, fontSize: 16 },
    link: { color: 'blue', marginTop: 10, textAlign: 'center' },
    error: { color: 'red', fontSize: 12, marginBottom: 5 },
    pickerContainer: { borderWidth: 1, borderRadius: 5, marginBottom: 10, },
    label: { fontSize: 16, fontWeight: '500', color: 'black' },
    pickLabel: { fontSize: 16, fontWeight: 'bold', color: 'grey' }
});
