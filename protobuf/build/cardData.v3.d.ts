import * as $protobuf from "protobufjs";
import Long = require("long");
/** Properties of a Header. */
export interface IHeader {

    /** Header university */
    university?: (number|null);

    /** Header institute */
    institute?: (number|null);

    /** Header branch */
    branch?: (number|null);

    /** Header schema */
    schema?: (number|null);
}

/** Represents a Header. */
export class Header implements IHeader {

    /**
     * Constructs a new Header.
     * @param [properties] Properties to set
     */
    constructor(properties?: IHeader);

    /** Header university. */
    public university: number;

    /** Header institute. */
    public institute: number;

    /** Header branch. */
    public branch: number;

    /** Header schema. */
    public schema: number;

    /**
     * Creates a new Header instance using the specified properties.
     * @param [properties] Properties to set
     * @returns Header instance
     */
    public static create(properties?: IHeader): Header;

    /**
     * Encodes the specified Header message. Does not implicitly {@link Header.verify|verify} messages.
     * @param message Header message or plain object to encode
     * @param [writer] Writer to encode to
     * @returns Writer
     */
    public static encode(message: IHeader, writer?: $protobuf.Writer): $protobuf.Writer;

    /**
     * Encodes the specified Header message, length delimited. Does not implicitly {@link Header.verify|verify} messages.
     * @param message Header message or plain object to encode
     * @param [writer] Writer to encode to
     * @returns Writer
     */
    public static encodeDelimited(message: IHeader, writer?: $protobuf.Writer): $protobuf.Writer;

    /**
     * Decodes a Header message from the specified reader or buffer.
     * @param reader Reader or buffer to decode from
     * @param [length] Message length if known beforehand
     * @returns Header
     * @throws {Error} If the payload is not a reader or valid buffer
     * @throws {$protobuf.util.ProtocolError} If required fields are missing
     */
    public static decode(reader: ($protobuf.Reader|Uint8Array), length?: number): Header;

    /**
     * Decodes a Header message from the specified reader or buffer, length delimited.
     * @param reader Reader or buffer to decode from
     * @returns Header
     * @throws {Error} If the payload is not a reader or valid buffer
     * @throws {$protobuf.util.ProtocolError} If required fields are missing
     */
    public static decodeDelimited(reader: ($protobuf.Reader|Uint8Array)): Header;

    /**
     * Verifies a Header message.
     * @param message Plain object to verify
     * @returns `null` if valid, otherwise the reason why it is not
     */
    public static verify(message: { [k: string]: any }): (string|null);

    /**
     * Creates a Header message from a plain object. Also converts values to their respective internal types.
     * @param object Plain object
     * @returns Header
     */
    public static fromObject(object: { [k: string]: any }): Header;

    /**
     * Creates a plain object from a Header message. Also converts values to other types if specified.
     * @param message Header
     * @param [options] Conversion options
     * @returns Plain object
     */
    public static toObject(message: Header, options?: $protobuf.IConversionOptions): { [k: string]: any };

    /**
     * Converts this Header to JSON.
     * @returns JSON object
     */
    public toJSON(): { [k: string]: any };

    /**
     * Gets the default type url for Header
     * @param [typeUrlPrefix] your custom typeUrlPrefix(default "type.googleapis.com")
     * @returns The default type url
     */
    public static getTypeUrl(typeUrlPrefix?: string): string;
}

/** Properties of a Meta. */
export interface IMeta {

    /** Meta id */
    id?: (string|null);

    /** Meta total */
    total?: (number|null);

    /** Meta other */
    other?: ({ [k: string]: string }|null);
}

/** Represents a Meta. */
export class Meta implements IMeta {

    /**
     * Constructs a new Meta.
     * @param [properties] Properties to set
     */
    constructor(properties?: IMeta);

    /** Meta id. */
    public id: string;

    /** Meta total. */
    public total: number;

    /** Meta other. */
    public other: { [k: string]: string };

    /**
     * Creates a new Meta instance using the specified properties.
     * @param [properties] Properties to set
     * @returns Meta instance
     */
    public static create(properties?: IMeta): Meta;

    /**
     * Encodes the specified Meta message. Does not implicitly {@link Meta.verify|verify} messages.
     * @param message Meta message or plain object to encode
     * @param [writer] Writer to encode to
     * @returns Writer
     */
    public static encode(message: IMeta, writer?: $protobuf.Writer): $protobuf.Writer;

    /**
     * Encodes the specified Meta message, length delimited. Does not implicitly {@link Meta.verify|verify} messages.
     * @param message Meta message or plain object to encode
     * @param [writer] Writer to encode to
     * @returns Writer
     */
    public static encodeDelimited(message: IMeta, writer?: $protobuf.Writer): $protobuf.Writer;

    /**
     * Decodes a Meta message from the specified reader or buffer.
     * @param reader Reader or buffer to decode from
     * @param [length] Message length if known beforehand
     * @returns Meta
     * @throws {Error} If the payload is not a reader or valid buffer
     * @throws {$protobuf.util.ProtocolError} If required fields are missing
     */
    public static decode(reader: ($protobuf.Reader|Uint8Array), length?: number): Meta;

    /**
     * Decodes a Meta message from the specified reader or buffer, length delimited.
     * @param reader Reader or buffer to decode from
     * @returns Meta
     * @throws {Error} If the payload is not a reader or valid buffer
     * @throws {$protobuf.util.ProtocolError} If required fields are missing
     */
    public static decodeDelimited(reader: ($protobuf.Reader|Uint8Array)): Meta;

    /**
     * Verifies a Meta message.
     * @param message Plain object to verify
     * @returns `null` if valid, otherwise the reason why it is not
     */
    public static verify(message: { [k: string]: any }): (string|null);

    /**
     * Creates a Meta message from a plain object. Also converts values to their respective internal types.
     * @param object Plain object
     * @returns Meta
     */
    public static fromObject(object: { [k: string]: any }): Meta;

    /**
     * Creates a plain object from a Meta message. Also converts values to other types if specified.
     * @param message Meta
     * @param [options] Conversion options
     * @returns Plain object
     */
    public static toObject(message: Meta, options?: $protobuf.IConversionOptions): { [k: string]: any };

    /**
     * Converts this Meta to JSON.
     * @returns JSON object
     */
    public toJSON(): { [k: string]: any };

    /**
     * Gets the default type url for Meta
     * @param [typeUrlPrefix] your custom typeUrlPrefix(default "type.googleapis.com")
     * @returns The default type url
     */
    public static getTypeUrl(typeUrlPrefix?: string): string;
}

/** Properties of a Subject. */
export interface ISubject {

    /** Subject subject */
    subject?: ({ [k: string]: IMeta }|null);
}

/** Represents a Subject. */
export class Subject implements ISubject {

    /**
     * Constructs a new Subject.
     * @param [properties] Properties to set
     */
    constructor(properties?: ISubject);

    /** Subject subject. */
    public subject: { [k: string]: IMeta };

    /**
     * Creates a new Subject instance using the specified properties.
     * @param [properties] Properties to set
     * @returns Subject instance
     */
    public static create(properties?: ISubject): Subject;

    /**
     * Encodes the specified Subject message. Does not implicitly {@link Subject.verify|verify} messages.
     * @param message Subject message or plain object to encode
     * @param [writer] Writer to encode to
     * @returns Writer
     */
    public static encode(message: ISubject, writer?: $protobuf.Writer): $protobuf.Writer;

    /**
     * Encodes the specified Subject message, length delimited. Does not implicitly {@link Subject.verify|verify} messages.
     * @param message Subject message or plain object to encode
     * @param [writer] Writer to encode to
     * @returns Writer
     */
    public static encodeDelimited(message: ISubject, writer?: $protobuf.Writer): $protobuf.Writer;

    /**
     * Decodes a Subject message from the specified reader or buffer.
     * @param reader Reader or buffer to decode from
     * @param [length] Message length if known beforehand
     * @returns Subject
     * @throws {Error} If the payload is not a reader or valid buffer
     * @throws {$protobuf.util.ProtocolError} If required fields are missing
     */
    public static decode(reader: ($protobuf.Reader|Uint8Array), length?: number): Subject;

    /**
     * Decodes a Subject message from the specified reader or buffer, length delimited.
     * @param reader Reader or buffer to decode from
     * @returns Subject
     * @throws {Error} If the payload is not a reader or valid buffer
     * @throws {$protobuf.util.ProtocolError} If required fields are missing
     */
    public static decodeDelimited(reader: ($protobuf.Reader|Uint8Array)): Subject;

    /**
     * Verifies a Subject message.
     * @param message Plain object to verify
     * @returns `null` if valid, otherwise the reason why it is not
     */
    public static verify(message: { [k: string]: any }): (string|null);

    /**
     * Creates a Subject message from a plain object. Also converts values to their respective internal types.
     * @param object Plain object
     * @returns Subject
     */
    public static fromObject(object: { [k: string]: any }): Subject;

    /**
     * Creates a plain object from a Subject message. Also converts values to other types if specified.
     * @param message Subject
     * @param [options] Conversion options
     * @returns Plain object
     */
    public static toObject(message: Subject, options?: $protobuf.IConversionOptions): { [k: string]: any };

    /**
     * Converts this Subject to JSON.
     * @returns JSON object
     */
    public toJSON(): { [k: string]: any };

    /**
     * Gets the default type url for Subject
     * @param [typeUrlPrefix] your custom typeUrlPrefix(default "type.googleapis.com")
     * @returns The default type url
     */
    public static getTypeUrl(typeUrlPrefix?: string): string;
}

/** Properties of a CardData. */
export interface ICardData {

    /** CardData header */
    header?: (IHeader|null);

    /** CardData semester */
    semester?: ({ [k: string]: ISubject }|null);

    /** CardData personal */
    personal?: ({ [k: string]: string }|null);

    /** CardData image */
    image?: ({ [k: string]: Uint8Array }|null);
}

/** Represents a CardData. */
export class CardData implements ICardData {

    /**
     * Constructs a new CardData.
     * @param [properties] Properties to set
     */
    constructor(properties?: ICardData);

    /** CardData header. */
    public header?: (IHeader|null);

    /** CardData semester. */
    public semester: { [k: string]: ISubject };

    /** CardData personal. */
    public personal: { [k: string]: string };

    /** CardData image. */
    public image: { [k: string]: Uint8Array };

    /**
     * Creates a new CardData instance using the specified properties.
     * @param [properties] Properties to set
     * @returns CardData instance
     */
    public static create(properties?: ICardData): CardData;

    /**
     * Encodes the specified CardData message. Does not implicitly {@link CardData.verify|verify} messages.
     * @param message CardData message or plain object to encode
     * @param [writer] Writer to encode to
     * @returns Writer
     */
    public static encode(message: ICardData, writer?: $protobuf.Writer): $protobuf.Writer;

    /**
     * Encodes the specified CardData message, length delimited. Does not implicitly {@link CardData.verify|verify} messages.
     * @param message CardData message or plain object to encode
     * @param [writer] Writer to encode to
     * @returns Writer
     */
    public static encodeDelimited(message: ICardData, writer?: $protobuf.Writer): $protobuf.Writer;

    /**
     * Decodes a CardData message from the specified reader or buffer.
     * @param reader Reader or buffer to decode from
     * @param [length] Message length if known beforehand
     * @returns CardData
     * @throws {Error} If the payload is not a reader or valid buffer
     * @throws {$protobuf.util.ProtocolError} If required fields are missing
     */
    public static decode(reader: ($protobuf.Reader|Uint8Array), length?: number): CardData;

    /**
     * Decodes a CardData message from the specified reader or buffer, length delimited.
     * @param reader Reader or buffer to decode from
     * @returns CardData
     * @throws {Error} If the payload is not a reader or valid buffer
     * @throws {$protobuf.util.ProtocolError} If required fields are missing
     */
    public static decodeDelimited(reader: ($protobuf.Reader|Uint8Array)): CardData;

    /**
     * Verifies a CardData message.
     * @param message Plain object to verify
     * @returns `null` if valid, otherwise the reason why it is not
     */
    public static verify(message: { [k: string]: any }): (string|null);

    /**
     * Creates a CardData message from a plain object. Also converts values to their respective internal types.
     * @param object Plain object
     * @returns CardData
     */
    public static fromObject(object: { [k: string]: any }): CardData;

    /**
     * Creates a plain object from a CardData message. Also converts values to other types if specified.
     * @param message CardData
     * @param [options] Conversion options
     * @returns Plain object
     */
    public static toObject(message: CardData, options?: $protobuf.IConversionOptions): { [k: string]: any };

    /**
     * Converts this CardData to JSON.
     * @returns JSON object
     */
    public toJSON(): { [k: string]: any };

    /**
     * Gets the default type url for CardData
     * @param [typeUrlPrefix] your custom typeUrlPrefix(default "type.googleapis.com")
     * @returns The default type url
     */
    public static getTypeUrl(typeUrlPrefix?: string): string;
}
