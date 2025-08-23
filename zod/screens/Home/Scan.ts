import * as z from "zod";
import { validNumber, validString } from '../../';


export const HeaderProto = z.object({
    university: validNumber,
    institute: validNumber,
    branch: validNumber,
});

export type HeaderProtoType = z.infer<typeof HeaderProto>;

export const PersonalProto = z.record(
    validString, validString
)

export type PersonalProtoType = z.infer<typeof PersonalProto>;

export const ImageProto = z.record(
    validString, z.instanceof(Uint8Array)
)

export type ImageProtoType = z.infer<typeof ImageProto>;

export const SubjectMeta = z.object({
    id: validString,
    total: validNumber,
    other: z.record(
        validString, validString
    )
})

export type SubjectMetaType = z.infer<typeof SubjectMeta>

export const SemesterMeta = z.object({
    subject: z.record(
        validString, SubjectMeta
    )
})

export type SemesterMetaType = z.infer<typeof SemesterMeta>


export const SemesterProto = z.record(
    validString, SemesterMeta
)

export type SemesterProtoType = z.infer<typeof SemesterProto>;

/** Protobuf Schema cause Protobuf ain't buffing */
export const CardProto = z.object({
    header: HeaderProto,
    personal: PersonalProto,
    semester: SemesterProto,
    image: ImageProto
})

export type CardProtoType = z.infer<typeof CardProto>;


export type ImageArray = {
    column: string,
    value: Uint8Array
}

export type PersonalArray = {
    column: string,
    value: string
}

export type SubjectMeta = {
    id: string,
    total: number,
    other: {
        [key: string]: string
    }
}

export type SubjectArray = {
    name: string,
    meta: SubjectMeta
}

export type SemesterData = {
    semester: string,
    subjects: SubjectArray[]
}

export const HeaderSchema = z.object({
    university: z.string().nullable(),
    institute: z.string().nullable(),
    branch: z.string().nullable()
})

export type HeaderType = z.infer<typeof HeaderSchema>;

export type useScanType = [
    boolean, 
    () => void,
    () => void
]
