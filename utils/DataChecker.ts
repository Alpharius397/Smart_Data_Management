import { CardJson } from "../../types/card";
import { JsTypes, JsTypesString } from "../../types/Home";

export function check_value(obj: JsTypes, type: string[]): boolean {
    try{
        return type.find((x) => x === typeof(obj)) !== undefined;
    } catch(error) {
        return false;
    }
}

export function check_object(obj: object, type_list: JsTypesString[][]): boolean {
    if(type_list.length === 0) return true;
    
    try{
        var res = true;

        if(typeof(obj) !== 'object'){
            res = res && check_value(obj, type_list[0]);
        } else {
            Object.keys(obj).forEach((key) => {
                res = res && check_value(key, type_list[0]) && check_object(obj[key], type_list.slice(1,));
            });
        }
        return res;
    }
    catch(error) {
        return false;
    }
}

export function check_format(jsonData: CardJson): boolean {

    try {
        const { university, institute, branch, images, sem_data, personal } = jsonData;

        if(!(
            check_value(university, ["string"]) &&
            check_value(institute, ["string"]) &&
            check_value(branch, ["string"]) &&
            check_object(images, [["string"], ["string"]]) &&
            check_object(personal, [["string"], ["string"]]) &&
            check_object(sem_data, [["string"], ["string"], ["string"], ["string", "number"]])
        )){
            throw new Error("Invalid Format")
        }

        return true;

    }
    catch(err) {
        console.warn(err);
        return false;
    }

}