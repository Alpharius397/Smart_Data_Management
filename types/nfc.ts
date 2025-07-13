import { CardJson } from "./card"

export type NfcJson = {
    ok: boolean,
    msg: string,
}

export type NfcCardJson = {
    ok: boolean,
    msg: CardJson,
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