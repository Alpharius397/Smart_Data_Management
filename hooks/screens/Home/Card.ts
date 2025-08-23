import { CardJson, CardJsonSchema } from '../../../zod/screens/Home/Card';
import { FetchNextPageOptions, InfiniteData, InfiniteQueryObserverResult, QueryObserverResult, RefetchOptions, useInfiniteQuery } from '@tanstack/react-query'
import Axios, { URL } from '../../../axios';
import { zodError } from '../../../zod';
import { isAxiosError } from 'axios';
import { DEFAULT_ERROR } from '../../../constants';


async function fetchCards({ pageParam = 0 }: {pageParam: number}): Promise<CardJson> {
    try {

        const response = await Axios.get(URL.CARD.CARDS, {
            params: {
                page: pageParam
            }
        });

        let a = await CardJsonSchema.parseAsync(response.data);

        return a;

    } catch(err){

        if(err instanceof zodError){
            console.warn(err)
            throw new Error("Received Invalid Data");
        }

        if(isAxiosError(err)){
            try {
                if(err.response?.status !== 500){
                    throw new Error("Unauthorized Fetch detected! Please logout and login")
                }
                else{
                    throw new Error(DEFAULT_ERROR);
                }
            } catch(eRR) {
                console.warn(eRR);
                throw new Error(DEFAULT_ERROR);
                
            }
        } else {
            throw new Error(DEFAULT_ERROR);
        }
    }

}

export function useCard(): {
    data: InfiniteData<CardJson, {pageParam: number}>,
    hasNextPage: boolean, 
    isFetchingNextPage: boolean, 
    fetchNextPage: (options: FetchNextPageOptions) => Promise<InfiniteQueryObserverResult<InfiniteData<CardJson, {pageParam: number}>, Error>>, 
    refetch: (options?: RefetchOptions) => Promise<QueryObserverResult<InfiniteData<CardJson, {pageParam: number}>, Error>>, 
    error: Error | null, 
    isError: boolean
}{

    const { data, fetchNextPage, refetch, isFetchingNextPage, hasNextPage, error, isError } = useInfiniteQuery<CardJson>({
        queryKey: ['cards'],
        //@ts-ignore
        queryFn: fetchCards,
        getNextPageParam: function (lastPage: CardJson, pages: CardJson[]): number | undefined {
            if(lastPage.cards.length < 5) return undefined;
            return lastPage.nextPage;
        },
    });

    //@ts-ignore
    return {data, hasNextPage, isFetchingNextPage, fetchNextPage, refetch, error, isError};
}