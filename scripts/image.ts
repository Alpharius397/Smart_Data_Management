import { Buffer } from "buffer";

export default function generate_image(a: Uint8Array): string {
    let b = Buffer.from(a).toString('base64');
    return `data:image/jpeg;base64,${b}`;
}