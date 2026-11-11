import { NextRequest, NextResponse } from 'next/server'
import { backendPublicApiFetch } from '@/lib/backend-api'

export const runtime = 'nodejs'

interface LookupRequestBody {
  customId?: string
  userType?: string
}

export async function POST(request: NextRequest) {
  try {
    const body = (await request.json()) as LookupRequestBody
    const customId = String(body.customId || '').trim().toUpperCase()
    const userType = String(body.userType || '').trim().toLowerCase()
    if (!customId || !['consumer', 'merchant'].includes(userType)) {
      return NextResponse.json(
        { error: 'customId and valid userType are required' },
        { status: 400 }
      )
    }

    type LookupResult = {
      userId: string
      username: string
      email?: string
      phone?: string
      fullName: string
      userType: string
      customId: string
    }
    const init = {
      method: 'POST',
      body: JSON.stringify({ customId, userType }),
    }
    let payload: LookupResult
    if (process.env.NODE_ENV === 'development') {
      try {
        payload = await backendPublicApiFetch<LookupResult>('/auth/mock/lookup', init)
      } catch (error) {
        if (!(error && typeof error === 'object' && 'status' in error && error.status === 404)) throw error
        payload = await backendPublicApiFetch<LookupResult>('/auth/lookup-id', init)
      }
    } else {
      payload = await backendPublicApiFetch<LookupResult>('/auth/lookup-id', init)
    }

    return NextResponse.json({
      userId: payload.userId,
      username: payload.username,
      email: payload.email,
      phone: payload.phone,
      fullName: payload.fullName,
      userType: payload.userType,
      customId: payload.customId,
    })
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Lookup failed'
    const status =
      typeof error === 'object' &&
      error !== null &&
      'status' in error &&
      typeof (error as { status: unknown }).status === 'number'
        ? (error as { status: number }).status
        : 500
    return NextResponse.json({ error: message }, { status })
  }
}
