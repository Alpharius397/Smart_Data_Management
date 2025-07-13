export type Dictionary<T, K> = {
    //@ts-ignore
    [key: T]: K 
}

export type CardJson = {
    university: string, 
    institute: string, 
    branch: string, 
    images:Dictionary<string, string>,
    sem_data: Dictionary<string, Dictionary<string, [string, number | string]>>,
    personal: Dictionary<string, string>
}