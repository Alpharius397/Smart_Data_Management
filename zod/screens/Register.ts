import * as z from "zod";
import { validNumber, validString } from ".."

export const registerSchema = z.object({
    username: validString,
    email: z.email({error: "Invalid Email Address"}),
    password: validString.min(10, {error: "Password must be have at least 10 characters"}),
    confirm_password: validString.min(10, {error: "Password must be have at least 10 characters"}),
    university: validNumber.gte(0),
    institute: validNumber.gte(0),
    branch: validNumber.gte(0),
}).refine((data) => data.password === data.confirm_password, {
    message: "Passwords must match",
    path: ["confirm_password"]
});

export const validItem = z.array(
    z.object({
        id: validNumber,
        name: validString
    })
)
export type Item = z.infer<typeof validItem>;

export type ItemResponse = {
    options: Item[]
}

export type RegisterFormData = z.infer<typeof registerSchema>
