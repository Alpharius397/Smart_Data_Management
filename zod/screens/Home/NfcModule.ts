import z from "zod"

export type NfcJson = {
    ok: boolean,
    msg: string,
}

export type NfcCardJson = {
    ok: boolean,
    data: string,
    uid: string
}

export interface NfcModuleType {
    isSupported(): Promise<boolean>,
    isEnabled(): Promise<boolean>,
    readyState(): Promise<NfcJson>
    startNfcScan(): Promise<void>
    DESFireCheck(): Promise<NfcJson>
    setListener(callback: () => void): void
    endNfcScan(): Promise<void>
}

export const subscriberSchema = z.object({
    status: z.boolean(),
    error: z.array(z.string()),
    key: z.string().nullable(),
    decryptionKey: z.string().nullable()
});

export type subscriberType = z.infer<typeof subscriberSchema>
