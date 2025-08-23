import * as z from "zod";
import { validEmail, validString } from '../..';

export const UserInfoSchema = z.object({
    username: validString,
    email: validEmail,
    university: validString,
    institute: validString,
    branch: validString,
});

export type UserInfo = z.infer<typeof UserInfoSchema>;

