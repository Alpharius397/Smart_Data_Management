export default function generate_image(a: string): string {
    let b = a.replaceAll("-", "+").replaceAll("_", "/");
    return `data:image/jpeg;base64,${b}`;
}