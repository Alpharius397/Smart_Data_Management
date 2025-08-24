import { createContext, useContext } from "react";

type ContextType = {
    card: string | null,
    setCard: (cardID: string) => void
}
export const Context = createContext({card: null, setCard: (cardID: string)=>{}});

export function useCard(): ContextType {
    return useContext(Context);
}
