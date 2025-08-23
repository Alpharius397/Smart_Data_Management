import z from "zod";
import { OTP } from "./Settings/Change";
import { validEmail, validPassword } from "..";

export const ForgotSchema = z.object({
    OTP: OTP,
    Email: validEmail,
    Password: validPassword,
    ConfirmPassword: validPassword,
}).refine((data) => (data.Password === data.ConfirmPassword),
    { message: "Passwords must match", path: ["ConfirmPassword"]}
)

export const ForgotPasswordSchema = z.object({
    Email: validEmail,
})

export type ForgotType = z.infer<typeof ForgotSchema>
export type ForgotPasswordType = z.infer<typeof ForgotPasswordSchema>