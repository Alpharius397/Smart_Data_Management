import * as z from "zod";
import { ZodError } from "zod";

export const userString = z.string().regex(/^[^/]+$/);

export const validString = z.string().nonempty({error: "This field cannot be empty"});
export const validNumber = z.number({error: "Value should be a number"});
export const validEmail = z.email({error: "Invalid email address"});
export const validPassword = validString.min(10, {error: "Password must be have at least 10 characters"});
export const zodError = ZodError

export const AuthResponse = z.object({
    status: z.boolean(),
    error: z.array(z.string()),
    access: z.string().nullable(),
    refresh: z.string().nullable()
})

export const QueryAuthResponse = z.discriminatedUnion("type", [
    z.object({
        type: z.literal("success"),
        status: z.literal(true),
        error: z.array(z.string()).length(0),
    }),
    z.object({
        type: z.literal("failure"),
        status: z.literal(false),            
        error: z.array(z.string()),
    }),
    z.object({
        type: z.literal("server-error"),
    }),
    z.object({
        type: z.literal("validation-error"),
        error: z.array(z.string()),
    }),
]);

export type QueryAuthType = z.infer<typeof QueryAuthResponse>
export type AuthType = z.infer<typeof AuthResponse>