import * as z from "zod";
import { validString } from '..';

export const LoginSchema = z.object({
    username: validString,
    password: validString
});

export type LoginForm = z.infer<typeof LoginSchema>;