import { ReactNode } from "react"
import * as z from "zod";
import { validString } from '../../';


export type LoadingParams = {
    children: ReactNode;
    loadingText: string
}

export const CardMetaSchema = z.object({
    cardID: validString,
    timestamp: z.coerce.date(),
    university: validString,
    institute: validString,
    branch: validString,
});

export const CardJsonSchema = z.object({
    cards: z.array(CardMetaSchema),
    nextPage: z.number().gte(0)
})

export const CardListSchema = z.array(CardMetaSchema);
export const CardRectSchema = z.array(z.object({
    cardID: validString,
    timestamp: z.date(),
    university: validString,
    institute: validString,
    branch: validString,
}));

export type CardMeta = z.infer<typeof CardMetaSchema>;
export type CardList = z.infer<typeof CardListSchema>;
export type CardReactList = z.infer<typeof CardRectSchema>;
export type CardJson = z.infer<typeof CardJsonSchema>;

