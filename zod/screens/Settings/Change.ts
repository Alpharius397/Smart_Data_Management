import * as z from "zod";
import { validEmail, validPassword, validString } from '../..';

export const OTP = z.string().regex(/^[0-9]{6}$/, {error: "OTP must have 6 numerical characters"})

export const UserNameChangeSchema = z.object({
    OTP: OTP,
    Username: validString
})

export const EmailChangeSchema = z.object({
    OTP: OTP,
    Email: validEmail
})

export const PasswordChangeSchema = z.object({
    OTP: OTP,
    Password: validPassword,
    ConfirmPassword: validPassword,
}).refine((data) => (data.Password === data.ConfirmPassword),
    { message: "Passwords must match", path: ["ConfirmPassword"]}
)

export const DeleteAccountSchema = z.object({
    OTP: OTP,
})

export const ForgotPasswordSchema = z.object({
    OTP: OTP,
})

export type UserNameType = z.infer<typeof UserNameChangeSchema>;
export type EmailType = z.infer<typeof EmailChangeSchema>;
export type PasswordType = z.infer<typeof PasswordChangeSchema>;
export type DeleteAccountType = z.infer<typeof DeleteAccountSchema>;
export type ForgotPasswordType = z.infer<typeof ForgotPasswordSchema>;